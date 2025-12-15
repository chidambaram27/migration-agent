"""Combined node for creating and validating Dockerfile with retry logic."""

import subprocess
from pathlib import Path
from langchain_core.messages import AIMessage
from agent.state import AgentState
from agent.tools.docker_tools import (
    read_dockerfile,
    is_multi_stage_dockerfile,
    write_dockerfile_argo
)
from agent.tools.llm_tools import convert_dockerfile_to_multi_stage


def create_and_validate_dockerfile_node(state: AgentState) -> AgentState:
    """Create and validate Dockerfile in a single node with retry logic.
    
    This node:
    1. Checks if build_platform has a value
    2. Reads the existing Dockerfile
    3. Checks if it's already multi-stage
    4. If not, converts it to multi-stage using LLM
    5. Writes the updated Dockerfile as Dockerfile-argo
    6. Validates the Dockerfile using docker buildx bake
    7. Retries up to max_retries times if validation fails
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with dockerfile_updated and validation results
    """
    clone_path = state.get("clone_path")
    dockerfile_path = state.get("dockerfile_path")
    build_platform = state.get("build_platform")
    build_as_config = state.get("build_as_config")
    docker_bake_file_path = state.get("docker_bake_file_path")
    
    # Initialize retry count and max retries if not set
    if state.get("dockerfile_validation_retry_count") is None:
        state["dockerfile_validation_retry_count"] = 0
    if state.get("dockerfile_validation_max_retries") is None:
        state["dockerfile_validation_max_retries"] = 2  # Default to 2 retries
    
    max_retries = state.get("dockerfile_validation_max_retries", 2)
    
    # Check if build_platform has a value
    if not build_platform:
        state["dockerfile_updated"] = False
        state["dockerfile_validation_passed"] = False
        state["messages"].append(
            AIMessage(content="⚠️ No build_platform found. Skipping Dockerfile update.")
        )
        return state
    
    # Check if clone_path and dockerfile_path are available
    if not clone_path:
        state["dockerfile_updated"] = False
        state["dockerfile_validation_passed"] = False
        state["error"] = "No clone path available for Dockerfile update"
        state["messages"].append(
            AIMessage(content="❌ Cannot update Dockerfile: No clone path available")
        )
        return state
    
    if not dockerfile_path:
        state["dockerfile_updated"] = False
        state["dockerfile_validation_passed"] = False
        state["error"] = "No Dockerfile path found"
        state["messages"].append(
            AIMessage(content="❌ Cannot update Dockerfile: No Dockerfile found in repository")
        )
        return state
    
    # Retry loop: create and validate until success or max retries reached
    retry_count = state.get("dockerfile_validation_retry_count", 0)
    validation_error = None
    
    while retry_count <= max_retries:
        # Step 1: Read Dockerfile (original or existing -argo file if retrying)
        if retry_count > 0 and validation_error:
            # Retry: read from existing -argo file
            dockerfile_argo_path = state.get("dockerfile_argo_path")
            if dockerfile_argo_path:
                full_dockerfile_path = Path(clone_path) / dockerfile_argo_path
                state["messages"].append(
                    AIMessage(content=f"🔄 Retry attempt {retry_count}/{max_retries}: Reading existing Dockerfile-argo at {dockerfile_argo_path}...")
                )
            else:
                # Fallback to original if -argo path not set
                full_dockerfile_path = Path(clone_path) / dockerfile_path
                state["messages"].append(
                    AIMessage(content=f"🔄 Retry attempt {retry_count}/{max_retries}: Reading Dockerfile at {dockerfile_path}...")
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
                state["dockerfile_validation_passed"] = False
                state["error"] = f"Dockerfile not found at {full_dockerfile_path}"
                state["messages"].append(
                    AIMessage(content=f"❌ Dockerfile not found at {full_dockerfile_path}")
                )
                return state
        except Exception as e:
            state["dockerfile_updated"] = False
            state["dockerfile_validation_passed"] = False
            state["error"] = f"Failed to read Dockerfile: {str(e)}"
            state["messages"].append(
                AIMessage(content=f"❌ Failed to read Dockerfile: {str(e)}")
            )
            return state
        
        # Step 2: Check if Dockerfile is already multi-stage (only on first attempt)
        if retry_count == 0 and is_multi_stage_dockerfile(dockerfile_content) and not validation_error:
            # If already multi-stage, create the -argo file by copying the content
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
            
            # Create the -argo file with the existing multi-stage content
            try:
                dockerfile_argo_path_full = Path(clone_path) / dockerfile_argo_path_str
                dockerfile_argo_path_full.write_text(dockerfile_content, encoding='utf-8')
                state["dockerfile_argo_path"] = dockerfile_argo_path_str
                state["dockerfile_updated"] = True
                state["messages"].append(
                    AIMessage(content=f"✅ Dockerfile is already multi-stage. Created Dockerfile-argo at {dockerfile_argo_path_str} for validation.")
                )
            except Exception as e:
                state["dockerfile_updated"] = False
                state["dockerfile_validation_passed"] = False
                state["error"] = f"Failed to create Dockerfile-argo: {str(e)}"
                state["messages"].append(
                    AIMessage(content=f"❌ Failed to create Dockerfile-argo: {str(e)}")
                )
                return state
        else:
            # Step 3: Convert to multi-stage (or retry with error context)
            if retry_count > 0:
                state["messages"].append(
                    AIMessage(content=f"🔄 Retrying Dockerfile conversion (attempt {retry_count + 1}/{max_retries + 1}) with validation error context...")
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
                state["dockerfile_validation_passed"] = False
                state["error"] = f"Failed to convert Dockerfile using LLM: {str(e)}"
                state["messages"].append(
                    AIMessage(content=f"❌ Failed to convert Dockerfile: {str(e)}")
                )
                return state
            
            # Step 4: Write the updated Dockerfile as Dockerfile-argo
            try:
                if retry_count > 0 and validation_error:
                    # Retry: write directly to the existing -argo file
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
                state["dockerfile_validation_passed"] = False
                state["error"] = f"Failed to write Dockerfile-argo: {str(e)}"
                state["messages"].append(
                    AIMessage(content=f"❌ Failed to write Dockerfile-argo: {str(e)}")
                )
                return state
        
        # Step 5: Validate the Dockerfile
        dockerfile_argo_path = state.get("dockerfile_argo_path")
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
                ["docker", "buildx", "bake", "-f", bake_file_name, "--set", "app.platform=linux/amd64"],
                cwd=str(bake_file_dir),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Validation passed!
                state["dockerfile_validation_passed"] = True
                state["dockerfile_validation_error"] = None
                state["dockerfile_validation_retry_count"] = retry_count
                state["messages"].append(
                    AIMessage(content="✅ Dockerfile validation passed! The Dockerfile is valid.")
                )
                return state
            else:
                # Validation failed - prepare for retry
                validation_error = result.stderr if result.stderr else result.stdout
                retry_count += 1
                state["dockerfile_validation_retry_count"] = retry_count
                state["dockerfile_validation_error"] = validation_error
                
                if retry_count > max_retries:
                    # Max retries reached
                    state["dockerfile_validation_passed"] = False
                    state["messages"].append(
                        AIMessage(content=f"❌ Dockerfile validation failed (attempt {retry_count}/{max_retries + 1}). Maximum retries reached. Error:\n{validation_error}")
                    )
                    return state
                else:
                    # Will retry
                    state["messages"].append(
                        AIMessage(content=f"❌ Dockerfile validation failed (attempt {retry_count}/{max_retries + 1}). Retrying with error context:\n{validation_error}")
                    )
                    # Continue loop to retry
                    continue
                
        except subprocess.TimeoutExpired:
            validation_error = "Dockerfile validation timed out after 5 minutes"
            retry_count += 1
            state["dockerfile_validation_retry_count"] = retry_count
            state["dockerfile_validation_error"] = validation_error
            
            if retry_count > max_retries:
                state["dockerfile_validation_passed"] = False
                state["messages"].append(
                    AIMessage(content=f"❌ Dockerfile validation timed out (attempt {retry_count}/{max_retries + 1}). Maximum retries reached.")
                )
                return state
            else:
                state["messages"].append(
                    AIMessage(content=f"❌ Dockerfile validation timed out (attempt {retry_count}/{max_retries + 1}). Retrying...")
                )
                continue
                
        except FileNotFoundError:
            validation_error = "Docker buildx not found. Please ensure Docker is installed and buildx is available."
            retry_count += 1
            state["dockerfile_validation_retry_count"] = retry_count
            state["dockerfile_validation_error"] = validation_error
            
            if retry_count > max_retries:
                state["dockerfile_validation_passed"] = False
                state["messages"].append(
                    AIMessage(content=f"❌ Docker buildx not found (attempt {retry_count}/{max_retries + 1}). Maximum retries reached. Please ensure Docker is installed.")
                )
                return state
            else:
                state["messages"].append(
                    AIMessage(content=f"❌ Docker buildx not found (attempt {retry_count}/{max_retries + 1}). Retrying...")
                )
                continue
                
        except Exception as e:
            validation_error = f"Unexpected error during validation: {str(e)}"
            retry_count += 1
            state["dockerfile_validation_retry_count"] = retry_count
            state["dockerfile_validation_error"] = validation_error
            
            if retry_count > max_retries:
                state["dockerfile_validation_passed"] = False
                state["messages"].append(
                    AIMessage(content=f"❌ Unexpected error during validation (attempt {retry_count}/{max_retries + 1}). Maximum retries reached: {str(e)}")
                )
                return state
            else:
                state["messages"].append(
                    AIMessage(content=f"❌ Unexpected error during validation (attempt {retry_count}/{max_retries + 1}). Retrying: {str(e)}")
                )
                continue
    
    # Should not reach here, but handle edge case
    state["dockerfile_validation_passed"] = False
    return state

