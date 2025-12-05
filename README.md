# LangGraph Repository Cloning Agent

A simple LangGraph agent workflow that clones a git repository from a given URL.

## Project Structure

```
.
├── agent/
│   ├── __init__.py      # Package initialization
│   ├── state.py         # State schema definition
│   ├── tools.py         # Repository cloning tools
│   ├── nodes.py         # Workflow nodes
│   └── graph.py         # LangGraph workflow definition
├── main.py              # Main entry point
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Features

- ✅ Validates repository URLs
- ✅ Clones git repositories to local filesystem
- ✅ Error handling and status reporting
- ✅ Clean, modular architecture following LangGraph best practices

## Installation

1. **Activate your virtual environment** (if using one):
   ```bash
   source myenv/bin/activate  # On macOS/Linux
   # or
   myenv\Scripts\activate     # On Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Command Line

```bash
python main.py <repository_url>
```

**Example:**
```bash
python main.py https://github.com/langchain-ai/langgraph.git
```

### Programmatic Usage

```python
from main import run_agent

result = run_agent("https://github.com/langchain-ai/langgraph.git")
print(f"Status: {result['status']}")
print(f"Clone Path: {result.get('clone_path')}")
```

## Workflow

The agent follows this workflow:

1. **Validate URL** - Checks if the repository URL is well-formed
2. **Clone Repository** - Executes `git clone` command
3. **Report Results** - Returns status and path information

## State Schema

The agent state includes:
- `messages`: List of conversation messages
- `repository_url`: The repository URL to clone
- `clone_path`: Local path where repository was cloned
- `status`: Current status (pending, validated, cloning, success, error)
- `error`: Error message if operation failed

## Requirements

- Python 3.8+
- Git installed and available in PATH
- LangGraph and LangChain Core packages

## Error Handling

The agent handles:
- Invalid repository URLs
- Network timeouts (5 minute limit)
- Existing directories
- Git command failures
- Unexpected errors

## Future Enhancements

Potential improvements:
- Support for branch/tag selection
- Custom clone directory specification
- Progress reporting during clone
- Support for private repositories with authentication
- Batch cloning multiple repositories

## License

MIT

