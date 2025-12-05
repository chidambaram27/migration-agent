"""Tools for LLM operations."""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage


def get_gemini_model():
    """Initialize and return a Gemini LLM model.
    
    Returns:
        ChatGoogleGenerativeAI instance configured with gemini-2.5-flash-lite
    """
    # Check if API key is set in environment variable
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set. Please set it in your .env file.")
    
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0.1  # Lower temperature for more deterministic output
    )


def convert_dockerfile_to_multi_stage(
    dockerfile_content: str,
    build_platform: str,
    build_as_config: str | None = None
) -> str:
    """Convert a single-stage Dockerfile to multi-stage using LLM.
    
    Args:
        dockerfile_content: Content of the existing Dockerfile
        build_platform: Build platform from CICD (e.g., 'python-pypi', 'java-gradle')
        build_as_config: Full content inside the buildAs block (e.g., "pythonVersion '3.7.9'")
        
    Returns:
        Updated multi-stage Dockerfile content
    """
    model = get_gemini_model()
    
    system_prompt = """You are an expert Docker engineer. Your task is to convert a single-stage Dockerfile to a multi-stage Dockerfile.

Important requirements:
1. Create a build stage that uses the appropriate base image based on the build_platform provided
2. Use the same version/configuration from the existing Dockerfile in the build stage
3. Keep the runtime stage EXACTLY as it is in the original Dockerfile - do not make major changes
4. Only copy necessary artifacts from the build stage to the runtime stage
5. Ensure the final image is optimized and follows Docker best practices
6. Preserve all original functionality, environment variables, and configurations from the runtime stage

Return ONLY the complete multi-stage Dockerfile content, without any explanations or markdown formatting."""
    
    # Build the build configuration section
    build_config_section = ""
    if build_as_config:
        build_config_section = f"""
Build Configuration from buildAs block: Use the below details to configure the build stage base image 
{build_as_config}

Use the specific versions and configurations from the buildAs block above (e.g., pythonVersion, gradleImage, jdkVersionMajor) to determine the exact base image and versions for the build stage."""
    else:
        build_config_section = f"\nBuild Platform: {build_platform}\nUse the appropriate base image for {build_platform} based on the existing Dockerfile."
    
    user_prompt = f"""Convert the following Dockerfile to a multi-stage build.
{build_config_section}

Original Dockerfile:
```
{dockerfile_content}
```

Create a multi-stage Dockerfile with:
1. A build stage that uses the appropriate base image and versions based on the buildAs configuration above
2. A runtime stage that keeps the existing runtime stage as-is (no major changes)

Return the complete multi-stage Dockerfile:"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    response = model.invoke(messages)
    content = response.content.strip()
    
    # Remove markdown code blocks if present
    if content.startswith("```"):
        # Remove opening ```dockerfile or ```
        lines = content.split('\n')
        if lines[0].startswith('```'):
            lines = lines[1:]
        # Remove closing ```
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        content = '\n'.join(lines)
    
    return content.strip()

