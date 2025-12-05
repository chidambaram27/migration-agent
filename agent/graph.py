"""LangGraph workflow definition for repository cloning."""

from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import validate_url_node, clone_repository_node, should_continue


def create_workflow() -> StateGraph:
    """Create the repository cloning workflow graph.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("validate_url", validate_url_node)
    workflow.add_node("clone_repository", clone_repository_node)
    
    # Set entry point
    workflow.set_entry_point("validate_url")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "validate_url",
        should_continue,
        {
            "clone": "clone_repository",
            "end": END
        }
    )
    
    # Add edge from clone to end
    workflow.add_edge("clone_repository", END)
    
    # Compile the graph
    return workflow.compile()


# Export the graph for LangGraph Studio
graph = create_workflow()

