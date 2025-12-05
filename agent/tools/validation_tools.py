from urllib.parse import urlparse

def validate_repository_url(repository_url: str) -> dict[str, bool | str]:
    """Validate if a repository URL is well-formed.
    
    Args:
        repository_url: The URL to validate
        
    Returns:
        Dictionary with 'valid' and 'message' keys
    """
    if not repository_url or not repository_url.strip():
        return {
            "valid": False,
            "message": "Repository URL cannot be empty"
        }
    
    parsed = urlparse(repository_url)
    
    # Check if it's a valid URL
    if not parsed.scheme:
        return {
            "valid": False,
            "message": "Repository URL must include a scheme (http://, https://, or git@)"
        }
    
    # Check for common git URL patterns
    valid_schemes = ["http", "https", "git", "ssh"]
    if parsed.scheme not in valid_schemes and not repository_url.startswith("git@"):
        return {
            "valid": False,
            "message": f"Invalid URL scheme. Must be one of: {', '.join(valid_schemes)} or git@ format"
        }
    
    return {
        "valid": True,
        "message": "Repository URL is valid"
    }

