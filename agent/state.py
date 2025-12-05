"""State definition for the repository cloning agent."""

from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """State schema for the repository cloning agent.
    
    Attributes:
        messages: List of messages in the conversation
        repository_url: The URL of the repository to clone
        clone_path: The local path where the repository will be cloned
        status: Current status of the operation (pending, cloning, success, error)
        error: Error message if operation failed
    """
    messages: Annotated[list[BaseMessage], add_messages]
    repository_url: str
    clone_path: str | None
    status: str
    error: str | None

# class MigrationState(TypedDict):
#     messages: Annotated[list, add_messages]
#     repo_url: str
#     local_path: str
#     dockerfiles: list[dict]  # {"path": str, "content": str}
#     updated_dockerfiles: list[dict]
#     validation_results: dict
#     workflows_added: list[str]
#     branch_name: str
#     git_status: str
#     human_approved: bool
