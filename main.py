"""Main entry point for the repository cloning agent."""

import sys
import os
from typing import Optional
from pathlib import Path
from langchain_core.messages import HumanMessage
from agent.state import AgentState

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # dotenv is optional, continue without it
    pass


def run_agent(repository_url: str, dockerfile_validation_max_retries: int = 2) -> dict:
    """Run the repository cloning agent.
    
    Args:
        repository_url: The URL of the repository to clone
        dockerfile_validation_max_retries: Maximum number of retries for dockerfile validation (default: 2)
        
    Returns:
        Final state dictionary
    """
    # Initialize state
    initial_state: AgentState = {
        "messages": [HumanMessage(content=f"Clone repository: {repository_url}")],
        "repository_url": repository_url,
        "clone_path": None,
        "status": "pending",
        "error": None,
        "via_cbs_file_content": None,
        "via_cbs_file_path": None,
        "dockerfile_path": None,
        "docker_bake_file_path": None,
        "build_platform": None,
        "build_as_config": None,
        "analysis_status": None,
        "dockerfile_updated": None,
        "dockerfile_argo_path": None,
        "dockerfile_validation_retry_count": None,
        "dockerfile_validation_max_retries": dockerfile_validation_max_retries,
        "dockerfile_validation_error": None,
        "dockerfile_validation_passed": None
    }
    
    # Get the workflow
    from agent.graph import create_workflow
    workflow = create_workflow()
    
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

