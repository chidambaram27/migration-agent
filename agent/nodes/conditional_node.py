from typing import Literal
from agent.state import AgentState

def should_continue(state: AgentState) -> Literal["clone", "end"]:
    """Determine the next step in the workflow.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node to execute
    """
    status = state.get("status", "")
    
    if status == "validated":
        return "clone"
    elif status in ["success", "error"]:
        return "end"
    else:
        return "end"


def should_update_dockerfile(state: AgentState) -> Literal["update_dockerfile", "copy_dependencies"]:
    """Determine if Dockerfile should be updated based on build_platform.
    
    Args:
        state: Current agent state
        
    Returns:
        "update_dockerfile" if build_platform has a value, "copy_dependencies" otherwise
    """
    build_platform = state.get("build_platform")
    
    if build_platform:
        return "update_dockerfile"
    else:
        return "copy_dependencies"


def should_update_dockerfile_after_deps(state: AgentState) -> Literal["update_dockerfile", "end"]:
    """Determine if Dockerfile should be updated after copying dependencies.
    
    Args:
        state: Current agent state
        
    Returns:
        "update_dockerfile" if build_platform has a value, "end" otherwise
    """
    build_platform = state.get("build_platform")
    
    if build_platform:
        return "update_dockerfile"
    else:
        return "end"


def should_retry_dockerfile_update(state: AgentState) -> Literal["update_dockerfile", "end"]:
    """Determine if Dockerfile update should be retried after validation failure.
    
    Args:
        state: Current agent state
        
    Returns:
        "update_dockerfile" if validation failed and retry limit not reached, "end" otherwise
    """
    validation_passed = state.get("dockerfile_validation_passed")
    retry_count = state.get("dockerfile_validation_retry_count", 0)
    max_retries = state.get("dockerfile_validation_max_retries", 2)
    
    # If validation passed, end
    if validation_passed:
        return "end"
    
    # If validation failed but we haven't exceeded max retries, retry
    if retry_count < max_retries:
        return "update_dockerfile"
    
    # If we've exceeded max retries, end
    return "end"

