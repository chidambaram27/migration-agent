"""Node for updating Dockerfile to multi-stage format."""

from pathlib import Path
from langchain_core.messages import AIMessage
from agent.state import AgentState
from agent.tools.docker_tools import (
    read_dockerfile,
    is_multi_stage_dockerfile,
    write_dockerfile_argo
)
from agent.tools.llm_tools import convert_dockerfile_to_multi_stage


def update_dockerfile_node(state: AgentState) -> AgentState:
    """Update Dockerfile to multi-stage format if needed.
    
    This node:
    1. Checks if build_platform has a value
    2. Reads the existing Dockerfile
    3. Checks if it's already multi-stage
    4. If already multi-stage, exits with a message
    5. If not, converts it to multi-stage using LLM
    6. Writes the updated Dockerfile as Dockerfile-argo
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with dockerfile_updated flag set
    """
    clone_path = state.get("clone_path")
    dockerfile_path = state.get("dockerfile_path")
    build_platform = state.get("build_platform")
    build_as_config = state.get("build_as_config")
    
    # Initialize retry count and max retries if not set
    if state.get("dockerfile_validation_retry_count") is None:
        state["dockerfile_validation_retry_count"] = 0
    if state.get("dockerfile_validation_max_retries") is None:
        state["dockerfile_validation_max_retries"] = 2  # Default to 2 retries
    
    # Check if build_platform has a value
    if not build_platform:
        state["dockerfile_updated"] = False
        state["messages"].append(
            AIMessage(content="⚠️ No build_platform found. Skipping Dockerfile update.")
        )
        return state
    
    # Check if clone_path and dockerfile_path are available
    if not clone_path:
        state["dockerfile_updated"] = False
        state["error"] = "No clone path available for Dockerfile update"
        state["messages"].append(
            AIMessage(content="❌ Cannot update Dockerfile: No clone path available")
        )
        return state
    
    if not dockerfile_path:
        state["dockerfile_updated"] = False
        state["error"] = "No Dockerfile path found"
        state["messages"].append(
            AIMessage(content="❌ Cannot update Dockerfile: No Dockerfile found in repository")
        )
        return state
    
    # Check if this is a retry after validation failure
    validation_error = state.get("dockerfile_validation_error")
    retry_count = state.get("dockerfile_validation_retry_count", 0)
    
    # If retrying, read from the existing -argo file, otherwise read from original
    if validation_error and retry_count > 0:
        dockerfile_argo_path = state.get("dockerfile_argo_path")
        if dockerfile_argo_path:
            # Read from existing -argo file
            full_dockerfile_path = Path(clone_path) / dockerfile_argo_path
            state["messages"].append(
                AIMessage(content=f"🔍 Reading existing Dockerfile-argo at {dockerfile_argo_path} for retry...")
            )
        else:
            # Fallback to original if -argo path not set
            full_dockerfile_path = Path(clone_path) / dockerfile_path
            state["messages"].append(
                AIMessage(content=f"🔍 Reading Dockerfile at {dockerfile_path} for retry...")
            )
    else:
        # First attempt: read from original Dockerfile
        full_dockerfile_path = Path(clone_path) / dockerfile_path
        state["messages"].append(
            AIMessage(content=f"🔍 Checking Dockerfile at {dockerfile_path}...")
        )
    
    # Read the Dockerfile
    try:
        dockerfile_content = read_dockerfile(str(full_dockerfile_path))
        if dockerfile_content is None:
            state["dockerfile_updated"] = False
            state["error"] = f"Dockerfile not found at {full_dockerfile_path}"
            state["messages"].append(
                AIMessage(content=f"❌ Dockerfile not found at {full_dockerfile_path}")
            )
            return state
    except Exception as e:
        state["dockerfile_updated"] = False
        state["error"] = f"Failed to read Dockerfile: {str(e)}"
        state["messages"].append(
            AIMessage(content=f"❌ Failed to read Dockerfile: {str(e)}")
        )
        return state
    
    # Check if Dockerfile is already multi-stage
    # Only skip update if it's already multi-stage AND there's no validation error (first attempt)
    validation_error = state.get("dockerfile_validation_error")
    if is_multi_stage_dockerfile(dockerfile_content) and not validation_error:
        # If already multi-stage and no validation error, construct the -argo path for consistency
        dockerfile_path_obj = Path(dockerfile_path)
        if dockerfile_path_obj.suffix:
            dockerfile_argo_name = dockerfile_path_obj.stem + "-argo" + dockerfile_path_obj.suffix
        else:
            dockerfile_argo_name = dockerfile_path_obj.name + "-argo"
        
        # Build the path: if parent is ".", just use the name, otherwise use parent/name
        if dockerfile_path_obj.parent == Path("."):
            dockerfile_argo_path_str = dockerfile_argo_name
        else:
            dockerfile_argo_path_str = str(dockerfile_path_obj.parent / dockerfile_argo_name)
        
        state["dockerfile_updated"] = True
        state["dockerfile_argo_path"] = dockerfile_argo_path_str
        state["messages"].append(
            AIMessage(content="✅ Dockerfile is already multi-stage. No update needed.")
        )
        return state
    
    if validation_error and retry_count > 0:
        state["messages"].append(
            AIMessage(content=f"🔄 Retrying Dockerfile conversion (attempt {retry_count + 1}) with validation error context...")
        )
    else:
        state["messages"].append(
            AIMessage(content=f"🔄 Converting Dockerfile to multi-stage format using build platform: {build_platform}...")
        )
    
    try:
        updated_dockerfile_content = convert_dockerfile_to_multi_stage(
            dockerfile_content,
            build_platform,
            build_as_config,
            validation_error
        )
    except Exception as e:
        state["dockerfile_updated"] = False
        state["error"] = f"Failed to convert Dockerfile using LLM: {str(e)}"
        state["messages"].append(
            AIMessage(content=f"❌ Failed to convert Dockerfile: {str(e)}")
        )
        return state
    
    # Write the updated Dockerfile as Dockerfile-argo
    try:
        # If retrying, write directly to the existing -argo file (full_dockerfile_path already points to it)
        # Otherwise, create a new -argo file from the original Dockerfile
        if validation_error and retry_count > 0:
            # Retry: write directly to the existing -argo file
            # full_dockerfile_path already points to the -argo file when retrying
            full_dockerfile_path.write_text(updated_dockerfile_content, encoding='utf-8')
            relative_argo_path = Path(full_dockerfile_path).relative_to(clone_path)
            state["dockerfile_argo_path"] = str(relative_argo_path)
            state["messages"].append(
                AIMessage(content=f"✅ Successfully updated multi-stage Dockerfile at {relative_argo_path}")
            )
        else:
            # First attempt: create new -argo file from original Dockerfile
            dockerfile_argo_path = write_dockerfile_argo(str(full_dockerfile_path), updated_dockerfile_content)
            relative_argo_path = Path(dockerfile_argo_path).relative_to(clone_path)
            state["dockerfile_argo_path"] = str(relative_argo_path)
            state["messages"].append(
                AIMessage(content=f"✅ Successfully created multi-stage Dockerfile at {relative_argo_path}")
            )
        
        state["dockerfile_updated"] = True
    except Exception as e:
        state["dockerfile_updated"] = False
        state["error"] = f"Failed to write Dockerfile-argo: {str(e)}"
        state["messages"].append(
            AIMessage(content=f"❌ Failed to write Dockerfile-argo: {str(e)}")
        )
        return state
    
    return state

