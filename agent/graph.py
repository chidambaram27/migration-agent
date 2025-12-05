"""LangGraph workflow definition for repository cloning."""

from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import (
    validate_url_node,
    clone_repository_node,
    analyze_repository_node,
    update_dockerfile_node,
    should_continue,
    should_update_dockerfile
)


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
    workflow.add_node("analyze_repository", analyze_repository_node)
    workflow.add_node("update_dockerfile", update_dockerfile_node)
    
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
    
    # Add edge from clone to analyze
    workflow.add_edge("clone_repository", "analyze_repository")
    
    # Add conditional edge from analyze to update_dockerfile or end
    workflow.add_conditional_edges(
        "analyze_repository",
        should_update_dockerfile,
        {
            "update_dockerfile": "update_dockerfile",
            "end": END
        }
    )
    
    # Add edge from update_dockerfile to end
    workflow.add_edge("update_dockerfile", END)
    
    # Compile the graph
    return workflow.compile()


# Export the graph for LangGraph Studio
graph = create_workflow()

