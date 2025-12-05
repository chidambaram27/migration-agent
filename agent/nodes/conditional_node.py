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

