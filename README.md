# App Vitals MCP

A collection of MCP servers built with FastMCP.

## Servers

- **Toggl Server** - Time tracking and productivity monitoring via Toggl API
- **Trello Server** - Card management and board operations via Trello API

## Installation

```bash
# Install dependencies
uv sync

# Install in development mode
pip install -e .
```

## Usage

Each server can be run independently:

```bash
# Toggl server
mcp-server-toggl

# Trello server
mcp-server-trello
```

## Development

The project uses:
- **FastMCP** for MCP server implementation
- **uv** for dependency management  
- **Pydantic** for data validation
- **httpx** for async HTTP requests

### Adding a New Server

1. Create a new directory under `src/app_vitals_mcp/servers/`
2. Implement the server using FastMCP
3. Add the entry point to `pyproject.toml`
4. Add documentation

### Testing

```bash
uv run pytest
```

### Linting

```bash
uv run ruff check
uv run mypy src/
```
