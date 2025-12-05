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
        via_cbs_file_content: Content of the ViaCBSfile
        via_cbs_file_path: Path to the ViaCBSfile in the repository
        dockerfile_path: Path to the Dockerfile
        docker_bake_file_path: Path to the docker-bake.hcl file if specified
        build_platform: Build platform extracted from buildAs argument (e.g., 'java-gradle', 'python-pypi')
        build_as_config: Full content inside the buildAs block (e.g., "pythonVersion '3.7.9'")
        analysis_status: Status of the analysis operation (pending, success, error)
        dockerfile_updated: Whether the Dockerfile was updated or was already multi-stage
    """
    messages: Annotated[list[BaseMessage], add_messages]
    repository_url: str
    clone_path: str | None
    status: str
    error: str | None
    via_cbs_file_content: str | None
    via_cbs_file_path: str | None
    dockerfile_path: str | None
    docker_bake_file_path: str | None
    build_platform: str | None
    build_as_config: str | None
    analysis_status: str | None
    dockerfile_updated: bool | None

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
