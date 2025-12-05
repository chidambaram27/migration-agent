"""Tools for the repository cloning agent."""

import os
import subprocess
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


def clone_repository(repository_url: str, target_dir: Optional[str] = "./workspace/") -> dict[str, str]:
    """Clone a git repository to a local directory.
    
    Args:
        repository_url: The URL of the repository to clone
        target_dir: Optional target directory. If not provided, uses repository name
        
    Returns:
        Dictionary with 'success', 'path', and 'message' keys
        
    Raises:
        ValueError: If repository URL is invalid
        subprocess.CalledProcessError: If git clone fails
    """
    # Validate URL
    if not repository_url or not repository_url.strip():
        return {
            "success": False,
            "path": "",
            "message": "Repository URL cannot be empty"
        }
    
    # Extract repository name from URL if target_dir not provided
    parsed_url = urlparse(repository_url)
    repo_name = os.path.basename(parsed_url.path)
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
    if not repo_name:
        repo_name = "cloned_repo"
    
    # Convert to Path object
    clone_path = Path(target_dir).resolve() / repo_name

    # Check if directory already exists
    if clone_path.exists():
        return {
            "success": True,
            "path": str(clone_path),
            "message": f"Directory {clone_path} already exists"
        }
    
    try:
        # Clone the repository
        result = subprocess.run(
            ["git", "clone", repository_url, str(clone_path)],
            capture_output=True,
            text=True,
            check=True,
            timeout=300  # 5 minute timeout
        )
        
        return {
            "success": True,
            "path": str(clone_path),
            "message": f"Successfully cloned repository to {clone_path}"
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "path": str(clone_path),
            "message": "Clone operation timed out after 5 minutes"
        }
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        return {
            "success": False,
            "path": str(clone_path),
            "message": f"Failed to clone repository: {error_msg}"
        }
    except Exception as e:
        return {
            "success": False,
            "path": str(clone_path),
            "message": f"Unexpected error: {str(e)}"
        }
