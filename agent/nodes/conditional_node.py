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


def should_update_dockerfile(state: AgentState) -> Literal["update_dockerfile", "end"]:
    """Determine if Dockerfile should be updated based on build_platform.
    
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

