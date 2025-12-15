"""LangGraph workflow definition for repository cloning."""

from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import (
    validate_url_node,
    clone_repository_node,
    analyze_repository_node,
    create_and_validate_dockerfile_node,
    copy_dependencies_node,
    should_continue,
    should_update_dockerfile_after_deps
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
    workflow.add_node("create_and_validate_dockerfile", create_and_validate_dockerfile_node)
    workflow.add_node("copy_dependencies", copy_dependencies_node)
    
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
    
    # Add edge from analyze to copy_dependencies (always copy dependencies first)
    workflow.add_edge("analyze_repository", "copy_dependencies")
    
    # Add conditional edge from copy_dependencies to create_and_validate_dockerfile or end
    workflow.add_conditional_edges(
        "copy_dependencies",
        should_update_dockerfile_after_deps,
        {
            "update_dockerfile": "create_and_validate_dockerfile",
            "end": END
        }
    )
    
    # Add edge from create_and_validate_dockerfile to end (retries are handled within the node)
    workflow.add_edge("create_and_validate_dockerfile", END)
    
    # Compile the graph
    return workflow.compile()


# Export the graph for LangGraph Studio
graph = create_workflow()

