"""Tools for LLM operations."""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_aws import ChatBedrockConverse 
import boto3



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

def get_anthorpic_model():
    # bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    bedrock_client = boto3.client("bedrock", region_name="us-east-1")
    llm = ChatBedrockConverse(
            # model="anthropic.claude-3-haiku-20240307-v1:0",
            model = "anthropic.claude-3-sonnet-20240229-v1:0",
            temperature=0,
            max_tokens=None,
            client=client,
            bedrock_client=bedrock_client
        )

    return llm


def convert_dockerfile_to_multi_stage(
    dockerfile_content: str,
    build_platform: str,
    build_as_config: str | None = None,
    validation_error: str | None = None
) -> str:
    """Convert a single-stage Dockerfile to multi-stage using LLM.
    
    Args:
        dockerfile_content: Content of the existing Dockerfile (or failed Dockerfile-argo if retrying)
        build_platform: Build platform from CICD (e.g., 'python-pypi', 'java-gradle')
        build_as_config: Full content inside the buildAs block (e.g., "pythonVersion '3.7.9'")
        validation_error: Error message from previous validation attempt (if retrying)
        
    Returns:
        Updated multi-stage Dockerfile content
    """
    # model = get_gemini_model()
    # For retries, use slightly higher temperature to encourage variation
   
    model = get_anthorpic_model()
    
    # Adjust system prompt based on whether this is a retry
    if validation_error:
        system_prompt = """You are an expert Docker engineer. Your task is to fix a multi-stage Dockerfile that failed validation.

CRITICAL: This is a RETRY attempt. The previous Dockerfile you generated failed validation. You MUST:
1. Carefully read and understand the validation error message
2. Identify the specific issues causing the validation failure
3. Fix ALL issues mentioned in the error
4. Do NOT repeat the same mistakes from the previous attempt
5. Generate a completely different, corrected Dockerfile that addresses the validation errors

Important requirements:
1. Create a build stage that uses the appropriate base image based on the build_platform provided
2. Use the same version/configuration from the existing Dockerfile in the build stage
3. Keep the runtime stage EXACTLY as it is in the original Dockerfile - do not make major changes
4. Only copy necessary artifacts from the build stage to the runtime stage
5. Ensure the final image is optimized and follows Docker best practices
6. Preserve all original functionality, environment variables, and configurations from the runtime stage
7. Fix any syntax errors, missing dependencies, incorrect paths, or build stage issues identified in the validation error

Return ONLY the complete corrected multi-stage Dockerfile content, without any explanations or markdown formatting."""
    else:
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
    
    # Build user prompt - put validation error at the TOP if retrying
    if validation_error:
        user_prompt = f"""🚨 RETRY ATTEMPT - PREVIOUS DOCKERFILE FAILED VALIDATION 🚨

CRITICAL VALIDATION ERROR (MUST FIX):
```
{validation_error}
```

The Dockerfile below failed validation with the error above. You MUST fix all issues mentioned in the error.

{build_config_section}

Current Dockerfile (that failed validation):
```
{dockerfile_content}
```

TASK: Fix the Dockerfile above by addressing ALL issues in the validation error. Generate a corrected multi-stage Dockerfile that:
1. Fixes all errors mentioned in the validation error message
2. Uses a build stage with the appropriate base image and versions based on the buildAs configuration
3. Keeps the runtime stage as-is (no major changes) but fixes any errors
4. Ensures all syntax is correct, all dependencies are present, and all paths are valid

Return the complete corrected multi-stage Dockerfile:"""
    else:
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
    
    # Handle both string and list content (Bedrock/Anthropic can return list)
    if isinstance(response.content, list):
        # Extract text from content blocks - handle both dict and string formats
        text_parts = []
        for block in response.content:
            if block:
                if isinstance(block, dict):
                    # Extract 'text' field from dictionary blocks
                    text_parts.append(block.get('text', ''))
                else:
                    # Handle string blocks
                    text_parts.append(str(block))
        content = ''.join(text_parts)
    else:
        content = str(response.content)
    
    content = content.strip()
    
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

