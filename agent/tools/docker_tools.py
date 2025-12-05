"""Tools for working with Dockerfiles."""

from pathlib import Path
from typing import Optional


def read_dockerfile(dockerfile_path: str) -> Optional[str]:
    """Read the content of a Dockerfile.
    
    Args:
        dockerfile_path: Path to the Dockerfile (can be relative or absolute)
        
    Returns:
        Content of the Dockerfile as a string, or None if file doesn't exist
    """
    dockerfile = Path(dockerfile_path)
    
    if not dockerfile.exists():
        return None
    
    try:
        return dockerfile.read_text(encoding='utf-8')
    except Exception as e:
        raise Exception(f"Failed to read Dockerfile: {str(e)}")


def is_multi_stage_dockerfile(dockerfile_content: str) -> bool:
    """Check if a Dockerfile is already multi-stage by counting FROM statements.
    
    Args:
        dockerfile_content: Content of the Dockerfile
        
    Returns:
        True if Dockerfile has multiple FROM statements (multi-stage), False otherwise
    """
    # Count FROM statements (case-insensitive, ignoring comments)
    lines = dockerfile_content.split('\n')
    from_count = 0
    
    for line in lines:
        # Strip whitespace and check if line starts with FROM (ignoring comments)
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            if stripped.upper().startswith('FROM'):
                from_count += 1
    
    return from_count > 1


def write_dockerfile_argo(dockerfile_path: str, content: str) -> str:
    """Write the updated Dockerfile as Dockerfile-argo in the same directory.
    
    Args:
        dockerfile_path: Path to the original Dockerfile
        content: Content to write to Dockerfile-argo
        
    Returns:
        Path to the created Dockerfile-argo file
    """
    original_dockerfile = Path(dockerfile_path)
    dockerfile_dir = original_dockerfile.parent
    dockerfile_argo_path = dockerfile_dir / "Dockerfile-argo"
    
    try:
        dockerfile_argo_path.write_text(content, encoding='utf-8')
        return str(dockerfile_argo_path)
    except Exception as e:
        raise Exception(f"Failed to write Dockerfile-argo: {str(e)}")

