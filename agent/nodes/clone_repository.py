from langchain_core.messages import AIMessage
from agent.state import AgentState
from agent.tools import clone_repository


def clone_repository_node(state: AgentState) -> AgentState:
    """Clone the repository.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with clone result
    """
    repository_url = state.get("repository_url", "")
    
    # Update status
    state["status"] = "cloning"
    state["messages"].append(
        AIMessage(content=f"🔄 Cloning repository from {repository_url}...")
    )
    
    # Perform clone
    result = clone_repository(repository_url, "./workspace/")
    
    if result["success"]:
        state["status"] = "success"
        state["clone_path"] = result["path"]
        state["error"] = None
        state["messages"].append(
            AIMessage(content=f"✅ {result['message']}")
        )
    else:
        state["status"] = "error"
        state["error"] = result["message"]
        state["messages"].append(
            AIMessage(content=f"❌ {result['message']}")
        )
    
    return state
