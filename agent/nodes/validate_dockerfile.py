"""Node for validating Dockerfile using docker buildx bake."""

import subprocess
from pathlib import Path
from langchain_core.messages import AIMessage
from agent.state import AgentState


def validate_dockerfile_node(state: AgentState) -> AgentState:
    """Validate the Dockerfile using docker buildx bake.
    
    This node:
    1. Checks if dockerfile_argo_path exists
    2. Runs `docker buildx bake -f docker-argo-bake.hcl` to validate
    3. Sets validation status and error message if it fails
    4. Increments retry counter if validation fails
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with validation results
    """
    clone_path = state.get("clone_path")
    dockerfile_argo_path = state.get("dockerfile_argo_path")
    docker_bake_file_path = state.get("docker_bake_file_path")
    retry_count = state.get("dockerfile_validation_retry_count", 0)
    
    # Check if clone_path is available
    if not clone_path:
        state["dockerfile_validation_passed"] = False
        state["dockerfile_validation_error"] = "No clone path available for Dockerfile validation"
        state["messages"].append(
            AIMessage(content="❌ Cannot validate Dockerfile: No clone path available")
        )
        return state
    
    # Check if dockerfile_argo_path exists
    if not dockerfile_argo_path:
        state["dockerfile_validation_passed"] = False
        state["dockerfile_validation_error"] = "No Dockerfile-argo path found for validation"
        state["messages"].append(
            AIMessage(content="❌ Cannot validate Dockerfile: No Dockerfile-argo found")
        )
        return state
    
    # Determine the docker-argo-bake.hcl file path
    if docker_bake_file_path:
        bake_file_path = Path(clone_path) / docker_bake_file_path
    else:
        # Default to docker-argo-bake.hcl in the same directory as the dockerfile
        dockerfile_path_obj = Path(clone_path) / dockerfile_argo_path
        bake_file_path = dockerfile_path_obj.parent / "docker-argo-bake.hcl"
    
    # Check if bake file exists
    if not bake_file_path.exists():
        state["dockerfile_validation_passed"] = False
        state["dockerfile_validation_error"] = f"Docker bake file not found at {bake_file_path.relative_to(clone_path)}"
        state["messages"].append(
            AIMessage(content=f"❌ Docker bake file not found at {bake_file_path.relative_to(clone_path)}")
        )
        return state
    
    # Get the directory where the bake file is located (for running the command)
    bake_file_dir = bake_file_path.parent
    bake_file_name = bake_file_path.name
    
    state["messages"].append(
        AIMessage(content=f"🔍 Validating Dockerfile using docker buildx bake -f {bake_file_name}...")
    )
    
    # Run docker buildx bake validation
    try:
        # Change to the directory containing the bake file and run the command
        result = subprocess.run(
            ["docker", "buildx", "bake", "-f", bake_file_name, "--set",  "app.platform=linux/amd64"],
            cwd=str(bake_file_dir),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            state["dockerfile_validation_passed"] = True
            state["dockerfile_validation_error"] = None
            state["dockerfile_validation_retry_count"] = retry_count
            state["messages"].append(
                AIMessage(content="✅ Dockerfile validation passed! The Dockerfile is valid.")
            )
        else:
            # Validation failed
            error_output = result.stderr if result.stderr else result.stdout
            new_retry_count = retry_count + 1
            max_retries = state.get("dockerfile_validation_max_retries", 2)
            state["dockerfile_validation_passed"] = False
            state["dockerfile_validation_error"] = error_output
            state["dockerfile_validation_retry_count"] = new_retry_count
            
            if new_retry_count >= max_retries:
                state["messages"].append(
                    AIMessage(content=f"❌ Dockerfile validation failed (attempt {new_retry_count}/{max_retries}). Maximum retries reached. Error:\n{error_output}")
                )
            else:
                state["messages"].append(
                    AIMessage(content=f"❌ Dockerfile validation failed (attempt {new_retry_count}/{max_retries}). Will retry with error context:\n{error_output}")
                )
            
    except subprocess.TimeoutExpired:
        new_retry_count = retry_count + 1
        max_retries = state.get("dockerfile_validation_max_retries", 2)
        state["dockerfile_validation_passed"] = False
        state["dockerfile_validation_error"] = "Dockerfile validation timed out after 5 minutes"
        state["dockerfile_validation_retry_count"] = new_retry_count
        if new_retry_count >= max_retries:
            state["messages"].append(
                AIMessage(content=f"❌ Dockerfile validation timed out (attempt {new_retry_count}/{max_retries}). Maximum retries reached.")
            )
        else:
            state["messages"].append(
                AIMessage(content=f"❌ Dockerfile validation timed out (attempt {new_retry_count}/{max_retries}). Will retry.")
            )
    except FileNotFoundError:
        new_retry_count = retry_count + 1
        max_retries = state.get("dockerfile_validation_max_retries", 2)
        state["dockerfile_validation_passed"] = False
        state["dockerfile_validation_error"] = "Docker buildx not found. Please ensure Docker is installed and buildx is available."
        state["dockerfile_validation_retry_count"] = new_retry_count
        if new_retry_count >= max_retries:
            state["messages"].append(
                AIMessage(content=f"❌ Docker buildx not found (attempt {new_retry_count}/{max_retries}). Maximum retries reached. Please ensure Docker is installed.")
            )
        else:
            state["messages"].append(
                AIMessage(content=f"❌ Docker buildx not found (attempt {new_retry_count}/{max_retries}). Will retry. Please ensure Docker is installed.")
            )
    except Exception as e:
        new_retry_count = retry_count + 1
        max_retries = state.get("dockerfile_validation_max_retries", 2)
        state["dockerfile_validation_passed"] = False
        state["dockerfile_validation_error"] = f"Unexpected error during validation: {str(e)}"
        state["dockerfile_validation_retry_count"] = new_retry_count
        if new_retry_count >= max_retries:
            state["messages"].append(
                AIMessage(content=f"❌ Unexpected error during validation (attempt {new_retry_count}/{max_retries}). Maximum retries reached: {str(e)}")
            )
        else:
            state["messages"].append(
                AIMessage(content=f"❌ Unexpected error during validation (attempt {new_retry_count}/{max_retries}). Will retry: {str(e)}")
            )
    
    return state

