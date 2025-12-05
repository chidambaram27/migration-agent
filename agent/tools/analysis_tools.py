"""Tools for analyzing repository files like ViaCBSfile and docker-bake.hcl."""

import re
from pathlib import Path
from typing import Optional, Dict, Any


def find_via_cbs_file(repo_path: str) -> Optional[Path]:
    """Find the ViaCBSfile in the repository.
    
    Args:
        repo_path: Path to the cloned repository
        
    Returns:
        Path to the ViaCBSfile if found, None otherwise
    """
    repo_dir = Path(repo_path)
    
    # Common names for ViaCBSfile
    possible_names = [
        "ViaCBSfile"
    ]
    
    for name in possible_names:
        file_path = repo_dir / name
        if file_path.exists() and file_path.is_file():
            return file_path
    
    return None


def read_via_cbs_file(file_path: Path) -> str:
    """Read the content of a ViaCBSfile.
    
    Args:
        file_path: Path to the ViaCBSfile
        
    Returns:
        Content of the file as a string
    """
    return file_path.read_text(encoding='utf-8')


def parse_docker_bake_file(file_path: Path) -> Optional[str]:
    """Parse docker-bake.hcl file to extract dockerfile path.
    
    Args:
        file_path: Path to the docker-bake.hcl file
        
    Returns:
        Dockerfile path if found, None otherwise
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Look for dockerfile = "..." pattern
        # This regex matches dockerfile = "path" or dockerfile = 'path'
        pattern = r'dockerfile\s*=\s*["\']([^"\']+)["\']'
        match = re.search(pattern, content, re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        return None
    except Exception:
        return None


def parse_via_cbs_file(content: str) -> Dict[str, Any]:
    """Parse ViaCBSfile content to extract relevant information.
    
    Args:
        content: Content of the ViaCBSfile
        
    Returns:
        Dictionary with parsed information:
        - docker_bake_file: Path to docker-bake.hcl if specified
        - build_platform: Build platform from buildAs argument (e.g., 'python-pypi', 'java-gradle')
        - build_as_config: Full content inside the buildAs block (e.g., "pythonVersion '3.7.9'")
        - has_docker_spec: Boolean indicating if docker is mentioned
    """
    result = {
        "docker_bake_file": None,
        "build_platform": None,
        "build_as_config": None,
        "has_docker_spec": False
    }
    
    # Check if docker is mentioned in the file
    docker_keywords = ['docker', 'Docker', 'DOCKER']
    result["has_docker_spec"] = any(keyword in content for keyword in docker_keywords)
    
    # Extract dockerBakeFile value
    # Pattern: dockerBakeFile './docker-bake.hcl' or dockerBakeFile "./docker-bake.hcl"
    docker_bake_pattern = r'dockerBakeFile\s+["\']([^"\']+)["\']'
    docker_bake_match = re.search(docker_bake_pattern, content, re.IGNORECASE)
    if docker_bake_match:
        result["docker_bake_file"] = docker_bake_match.group(1)
    
    # Extract buildAs block content
    # Pattern: buildAs('java-gradle') { ... } or buildAs("python-pypi") { ... }
    build_as_pattern = r'buildAs\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\{'
    build_as_match = re.search(build_as_pattern, content, re.IGNORECASE | re.DOTALL)
    if build_as_match:
        platform_name = build_as_match.group(1)
        result["build_platform"] = platform_name
        
        # Find the start of the block content (after the opening brace)
        block_start = build_as_match.end()
        
        # Find the matching closing brace by counting braces
        brace_count = 1
        i = block_start
        block_end = None
        
        while i < len(content) and brace_count > 0:
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    block_end = i
                    break
            i += 1
        
        # Extract the block content (everything between the braces)
        if block_end is not None and block_end > block_start:
            block_content = content[block_start:block_end].strip()
            result["build_as_config"] = block_content
    
    return result


def find_dockerfile_in_root(repo_path: str) -> Optional[Path]:
    """Check if Dockerfile exists in the root of the repository.
    
    Args:
        repo_path: Path to the cloned repository
        
    Returns:
        Path to Dockerfile if found, None otherwise
    """
    repo_dir = Path(repo_path)
    dockerfile_path = repo_dir / "Dockerfile"
    
    if dockerfile_path.exists() and dockerfile_path.is_file():
        return dockerfile_path
    
    return None

