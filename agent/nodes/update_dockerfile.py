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
    
    # Resolve full path to Dockerfile
    full_dockerfile_path = Path(clone_path) / dockerfile_path
    
    state["messages"].append(
        AIMessage(content=f"🔍 Checking Dockerfile at {dockerfile_path}...")
    )
    
    # Read the Dockerfile
    try:
        dockerfile_content = read_dockerfile(str(full_dockerfile_path))
        if dockerfile_content is None:
            state["dockerfile_updated"] = False
            state["error"] = f"Dockerfile not found at {dockerfile_path}"
            state["messages"].append(
                AIMessage(content=f"❌ Dockerfile not found at {dockerfile_path}")
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
    if is_multi_stage_dockerfile(dockerfile_content):
        state["dockerfile_updated"] = True
        state["messages"].append(
            AIMessage(content="✅ Dockerfile is already multi-stage. No update needed.")
        )
        return state
    
    # Convert to multi-stage using LLM
    state["messages"].append(
        AIMessage(content=f"🔄 Converting Dockerfile to multi-stage format using build platform: {build_platform}...")
    )
    
    try:
        updated_dockerfile_content = convert_dockerfile_to_multi_stage(
            dockerfile_content,
            build_platform,
            build_as_config
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
        dockerfile_argo_path = write_dockerfile_argo(str(full_dockerfile_path), updated_dockerfile_content)
        relative_argo_path = Path(dockerfile_argo_path).relative_to(clone_path)
        state["dockerfile_updated"] = True
        state["messages"].append(
            AIMessage(content=f"✅ Successfully created multi-stage Dockerfile at {relative_argo_path}")
        )
    except Exception as e:
        state["dockerfile_updated"] = False
        state["error"] = f"Failed to write Dockerfile-argo: {str(e)}"
        state["messages"].append(
            AIMessage(content=f"❌ Failed to write Dockerfile-argo: {str(e)}")
        )
        return state
    
    return state

