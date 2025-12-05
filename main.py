"""Main entry point for the repository cloning agent."""

import sys
from typing import Optional
from langchain_core.messages import HumanMessage
from agent.graph import get_workflow
from agent.state import AgentState


def run_agent(repository_url: str) -> dict:
    """Run the repository cloning agent.
    
    Args:
        repository_url: The URL of the repository to clone
        
    Returns:
        Final state dictionary
    """
    # Initialize state
    initial_state: AgentState = {
        "messages": [HumanMessage(content=f"Clone repository: {repository_url}")],
        "repository_url": repository_url,
        "clone_path": None,
        "status": "pending",
        "error": None
    }
    
    # Get the workflow
    workflow = get_workflow()
    
    # Run the workflow
    try:
        final_state = workflow.invoke(initial_state)
        return final_state
    except Exception as e:
        return {
            "messages": initial_state["messages"],
            "repository_url": repository_url,
            "clone_path": None,
            "status": "error",
            "error": f"Workflow execution failed: {str(e)}"
        }


def main():
    """Main function for CLI usage."""
    if len(sys.argv) < 2:
        print("Usage: python main.py <repository_url>")
        print("\nExample:")
        print("  python main.py https://github.com/langchain-ai/langgraph.git")
        sys.exit(1)
    
    repository_url = sys.argv[1]
    
    print(f"🚀 Starting repository cloning workflow...")
    print(f"📦 Repository URL: {repository_url}\n")
    
    # Run the agent
    result = run_agent(repository_url)
    
    # Print results
    print("\n" + "="*60)
    print("📊 Workflow Results")
    print("="*60)
    print(f"Status: {result['status']}")
    
    if result.get("clone_path"):
        print(f"Clone Path: {result['clone_path']}")
    
    if result.get("error"):
        print(f"Error: {result['error']}")
    
    print("\n📝 Messages:")
    for message in result.get("messages", []):
        print(f"  - {message.content}")
    
    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()

