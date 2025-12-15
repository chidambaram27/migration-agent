"""Node for copying and rendering dependency templates to the cloned repository."""

import re
from pathlib import Path
from jinja2 import Environment, BaseLoader
from langchain_core.messages import AIMessage
from agent.state import AgentState


def parse_github_url(github_url: str) -> tuple[str, str]:
    """Parse GitHub URL to extract organization and repository name.
    
    Supports formats:
    - https://github.com/org/repo
    - https://github.com/org/repo.git
    - git@github.com:org/repo.git
    - org/repo
    
    Args:
        github_url: GitHub repository URL or org/repo format
        
    Returns:
        Tuple of (github_org, repo_name)
        
    Raises:
        ValueError: If URL cannot be parsed
    """
    # Handle org/repo format
    if "/" in github_url and "github.com" not in github_url and "@" not in github_url:
        parts = github_url.split("/")
        if len(parts) >= 2:
            return parts[0], parts[1].replace(".git", "")
    
    # Handle full URLs
    # Extract org/repo from various URL formats
    patterns = [
        r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?/?$",  # https://github.com/org/repo or git@github.com:org/repo.git
        r"([^/]+)/([^/]+?)(?:\.git)?$",  # Fallback for org/repo
    ]
    
    for pattern in patterns:
        match = re.search(pattern, github_url)
        if match:
            org = match.group(1)
            repo = match.group(2).replace(".git", "")
            return org, repo
    
    raise ValueError(f"Could not parse GitHub URL: {github_url}")


def render_template(template_content: str, context: dict) -> str:
    """Render a Jinja2 template with custom delimiters [[ ]] instead of {{ }}.
    
    Args:
        template_content: Template content with [[ variable ]] placeholders
        context: Dictionary of variables to substitute
        
    Returns:
        Rendered template content
    """
    # Create Jinja2 environment with custom delimiters
    env = Environment(
        loader=BaseLoader(),
        variable_start_string='[[',
        variable_end_string=']]',
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    template = env.from_string(template_content)
    return template.render(**context)


def copy_dependencies_node(state: AgentState) -> AgentState:
    """Copy and render dependency templates to the cloned repository.
    
    This node:
    1. Parses github_url to extract github_org and repo_name
    2. Gets dockerfile_path from state
    3. Renders GHA templates and copies them to .github/workflows/
    4. Renders Docker template and copies it to root
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with dependency copy status
    """
    clone_path = state.get("clone_path")
    repository_url = state.get("repository_url", "")
    dockerfile_path = state.get("dockerfile_path")
    
    # Validate required state
    if not clone_path:
        state["error"] = "No clone path available for copying dependencies"
        state["messages"].append(
            AIMessage(content="❌ Cannot copy dependencies: No clone path available")
        )
        return state
    
    if not repository_url:
        state["error"] = "No repository URL available"
        state["messages"].append(
            AIMessage(content="❌ Cannot copy dependencies: No repository URL available")
        )
        return state
    
    if not dockerfile_path:
        state["error"] = "No dockerfile_path available"
        state["messages"].append(
            AIMessage(content="❌ Cannot copy dependencies: No dockerfile_path in state")
        )
        return state
    
    # Parse GitHub URL
    try:
        github_org, repo_name = parse_github_url(repository_url)
        state["messages"].append(
            AIMessage(content=f"📋 Parsed GitHub URL: org={github_org}, repo={repo_name}")
        )
    except ValueError as e:
        state["error"] = str(e)
        state["messages"].append(
            AIMessage(content=f"❌ Failed to parse GitHub URL: {str(e)}")
        )
        return state
    
    # Determine the dockerfile path to use in templates
    # Prefer dockerfile_argo_path if available, otherwise construct it from dockerfile_path
    dockerfile_path_for_template = state.get("dockerfile_argo_path")
    if not dockerfile_path_for_template:
        # Construct -argo path from original dockerfile_path
        dockerfile_path_obj = Path(dockerfile_path)
        if dockerfile_path_obj.suffix:
            dockerfile_argo_name = dockerfile_path_obj.stem + "-argo" + dockerfile_path_obj.suffix
        else:
            dockerfile_argo_name = dockerfile_path_obj.name + "-argo"
        
        # Build the path: if parent is ".", just use the name, otherwise use parent/name
        if dockerfile_path_obj.parent == Path("."):
            dockerfile_path_for_template = dockerfile_argo_name
        else:
            dockerfile_path_for_template = str(dockerfile_path_obj.parent / dockerfile_argo_name)
    
    # Prepare template context
    context = {
        "github_org": github_org,
        "repo_name": repo_name,
        "dockerfile_path": dockerfile_path_for_template
    }
    
    # Get paths
    clone_path_obj = Path(clone_path)
    dependencies_path = Path(__file__).parent.parent.parent / "dependencies"
    workflows_dir = clone_path_obj / ".github" / "workflows"
    
    # Create .github/workflows directory if it doesn't exist
    try:
        workflows_dir.mkdir(parents=True, exist_ok=True)
        state["messages"].append(
            AIMessage(content=f"📁 Created/verified .github/workflows directory")
        )
    except Exception as e:
        state["error"] = f"Failed to create .github/workflows directory: {str(e)}"
        state["messages"].append(
            AIMessage(content=f"❌ Failed to create .github/workflows directory: {str(e)}")
        )
        return state
    
    # Copy and render GHA templates
    gha_templates_dir = dependencies_path / "gha"
    copied_files = []
    
    try:
        for template_file in gha_templates_dir.glob("*.tpl"):
            # Read template
            template_content = template_file.read_text()
            
            # Render template
            rendered_content = render_template(template_content, context)
            
            # Write to .github/workflows/ without .tpl extension
            output_filename = template_file.stem  # Removes .tpl extension
            output_path = workflows_dir / output_filename
            
            output_path.write_text(rendered_content)
            copied_files.append(f".github/workflows/{output_filename}")
            
            state["messages"].append(
                AIMessage(content=f"✅ Copied and rendered {output_filename}")
            )
    except Exception as e:
        state["error"] = f"Failed to copy GHA templates: {str(e)}"
        state["messages"].append(
            AIMessage(content=f"❌ Failed to copy GHA templates: {str(e)}")
        )
        return state
    
    # Copy and render Docker template
    docker_templates_dir = dependencies_path / "docker"
    
    try:
        for template_file in docker_templates_dir.glob("*.tpl"):
            # Read template
            template_content = template_file.read_text()
            
            # Render template
            rendered_content = render_template(template_content, context)
            
            # Write to root without .tpl extension
            output_filename = template_file.stem  # Removes .tpl extension
            output_path = clone_path_obj / output_filename
            
            output_path.write_text(rendered_content)
            copied_files.append(output_filename)
            
            state["messages"].append(
                AIMessage(content=f"✅ Copied and rendered {output_filename} to root")
            )
    except Exception as e:
        state["error"] = f"Failed to copy Docker template: {str(e)}"
        state["messages"].append(
            AIMessage(content=f"❌ Failed to copy Docker template: {str(e)}")
        )
        return state
    
    # Success message
    state["messages"].append(
        AIMessage(content=f"✅ Successfully copied {len(copied_files)} dependency files: {', '.join(copied_files)}")
    )
    
    return state

