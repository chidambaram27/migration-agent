"""Node for analyzing the cloned repository to extract ViaCBSfile and Dockerfile information."""

from pathlib import Path
from langchain_core.messages import AIMessage
from agent.state import AgentState
from agent.tools.analysis_tools import (
    find_via_cbs_file,
    read_via_cbs_file,
    parse_via_cbs_file,
    parse_docker_bake_file,
    find_dockerfile_in_root
)


def analyze_repository_node(state: AgentState) -> AgentState:
    """Analyze the cloned repository to extract ViaCBSfile and Dockerfile information.
    
    This node:
    1. Finds and reads the ViaCBSfile
    2. Parses it to extract dockerBakeFile and buildAs information
    3. Determines the Dockerfile location
    4. Updates the state with all extracted information
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with analysis results
    """
    clone_path = state.get("clone_path")
    
    if not clone_path:
        state["analysis_status"] = "error"
        state["error"] = "No clone path available for analysis"
        state["messages"].append(
            AIMessage(content="❌ Cannot analyze repository: No clone path available")
        )
        return state
    
    # Update status
    state["analysis_status"] = "pending"
    state["messages"].append(
        AIMessage(content="🔍 Analyzing repository structure...")
    )
    
    # Step 1: Find and read ViaCBSfile
    via_cbs_file_path = find_via_cbs_file(clone_path)
    
    if not via_cbs_file_path:
        state["analysis_status"] = "error"
        state["error"] = "ViaCBSfile not found in repository"
        state["via_cbs_file_path"] = None
        state["via_cbs_file_content"] = None
        state["messages"].append(
            AIMessage(content="❌ ViaCBSfile not found in repository. Analysis cannot proceed.")
        )
        return state
    
    # Read ViaCBSfile content
    try:
        via_cbs_content = read_via_cbs_file(via_cbs_file_path)
        state["via_cbs_file_path"] = str(via_cbs_file_path.relative_to(clone_path))
        state["via_cbs_file_content"] = via_cbs_content
        state["messages"].append(
            AIMessage(content=f"✅ Found ViaCBSfile at {state['via_cbs_file_path']}")
        )
    except Exception as e:
        state["analysis_status"] = "error"
        state["error"] = f"Failed to read ViaCBSfile: {str(e)}"
        state["messages"].append(
            AIMessage(content=f"❌ Failed to read ViaCBSfile: {str(e)}")
        )
        return state
    
    # Step 2: Parse ViaCBSfile
    parsed_info = parse_via_cbs_file(via_cbs_content)
    
    # Step 3: Identify Dockerfile location
    dockerfile_path = None
    docker_bake_file_path = None
    
    if parsed_info["docker_bake_file"]:
        # If dockerBakeFile is specified, read it and extract dockerfile path
        repo_dir = Path(clone_path)
        # Remove leading ./ if present
        bake_file_relative = parsed_info["docker_bake_file"]
        if bake_file_relative.startswith('./'):
            bake_file_relative = bake_file_relative[2:]
        bake_file_path = repo_dir / bake_file_relative
        
        if bake_file_path.exists():
            docker_bake_file_path = str(bake_file_path.relative_to(clone_path))
            state["docker_bake_file_path"] = docker_bake_file_path
            state["messages"].append(
                AIMessage(content=f"✅ Found docker-bake file at {docker_bake_file_path}")
            )
            
            # Parse docker-bake.hcl to find dockerfile path
            dockerfile_from_bake = parse_docker_bake_file(bake_file_path)
            if dockerfile_from_bake:
                # Resolve relative path from bake file location
                bake_dir = bake_file_path.parent
                resolved_dockerfile = bake_dir / dockerfile_from_bake
                # Normalize the path (resolve relative paths like ../)
                resolved_dockerfile = resolved_dockerfile.resolve()
                repo_dir_path = Path(clone_path).resolve()
                
                # Check if the resolved dockerfile is within the repo directory
                try:
                    relative_dockerfile = resolved_dockerfile.relative_to(repo_dir_path)
                    if resolved_dockerfile.exists():
                        dockerfile_path = str(relative_dockerfile)
                        state["messages"].append(
                            AIMessage(content=f"✅ Found Dockerfile path from bake file: {dockerfile_path}")
                        )
                except ValueError:
                    # Dockerfile path is outside the repository
                    state["messages"].append(
                        AIMessage(content=f"⚠️ Dockerfile path from bake file is outside repository: {dockerfile_from_bake}")
                    )
        else:
            state["messages"].append(
                AIMessage(content=f"⚠️ docker-bake file specified but not found: {parsed_info['docker_bake_file']}")
            )
    
    # If no dockerfile found yet, check root
    # This handles cases where:
    # 1. No docker specification in ViaCBSfile
    # 2. dockerBakeFile was specified but dockerfile path wasn't found in it
    # 3. docker specification exists but no dockerBakeFile was specified
    if not dockerfile_path:
        root_dockerfile = find_dockerfile_in_root(clone_path)
        if root_dockerfile:
            dockerfile_path = str(root_dockerfile.relative_to(clone_path))
            state["messages"].append(
                AIMessage(content=f"✅ Found Dockerfile in repository root: {dockerfile_path}")
            )
        else:
            state["messages"].append(
                AIMessage(content="⚠️ No Dockerfile found in repository root")
            )
    
    # Step 4: Extract build platform and config from buildAs
    build_platform = parsed_info.get("build_platform")
    build_as_config = parsed_info.get("build_as_config")
    if build_platform:
        state["build_platform"] = build_platform
        state["messages"].append(
            AIMessage(content=f"✅ Identified build platform: {build_platform}")
        )
        if build_as_config:
            state["build_as_config"] = build_as_config
            state["messages"].append(
                AIMessage(content=f"✅ Extracted buildAs configuration: {build_as_config}")
            )
    else:
        state["build_platform"] = None
        state["build_as_config"] = None
        state["messages"].append(
            AIMessage(content="ℹ️ No buildAs argument found in ViaCBSfile")
        )
    
    # Update state with dockerfile path
    state["dockerfile_path"] = dockerfile_path
    
    # Mark analysis as successful
    state["analysis_status"] = "success"
    state["messages"].append(
        AIMessage(content="✅ Repository analysis completed successfully")
    )
    
    return state

