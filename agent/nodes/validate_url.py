from langchain_core.messages import AIMessage
from agent.state import AgentState
from agent.tools import validate_repository_url


def validate_url_node(state: AgentState) -> AgentState:
    """Validate the repository URL.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with validation result
    """
    repository_url = state.get("repository_url", "")
    
    validation = validate_repository_url(repository_url)
    
    if validation["valid"]:
        state["status"] = "validated"
        print(f'Repository URL Validated')
        state["messages"].append(
            AIMessage(content=f"✓ Repository URL is valid: {repository_url}")
        )
    else:
        state["status"] = "error"
        state["error"] = validation["message"]
        print(f'Repository URL Not Valid')
        state["messages"].append(
            AIMessage(content=f"✗ Validation failed: {validation['message']}")
        )
    
    return state
