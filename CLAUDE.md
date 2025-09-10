# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
# Install dependencies
uv sync

# Install in development mode
pip install -e .
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/servers/toggl/test_server.py

# Run with coverage
uv run pytest --cov=src/app_vitals_mcp
```

### Linting and Type Checking
```bash
# Run ruff linter
uv run ruff check

# Fix auto-fixable issues
uv run ruff check --fix

# Run type checking
uv run mypy src/
```

### Running Servers
```bash
# Run Toggl server
mcp-server-toggl

# Run Trello server
mcp-server-trello

# Servers require environment variables - see server's config.py for required vars
```

## Architecture

This is a collection of MCP (Model Context Protocol) servers built with FastMCP framework. Each server follows a layered architecture pattern:

### Server Structure Pattern
Each server in `src/app_vitals_mcp/servers/` follows this structure:
- `server.py` - Main MCP server class that sets up tools and coordinates services
- `client.py` - HTTP client wrapper for external API communication
- `services.py` - Business logic layer containing service classes for different domains
- `models.py` - Pydantic models for data validation and serialization
- `config.py` - Configuration management using environment variables
- `main.py` - Entry point that initializes and runs the server

### Service Layer Pattern
Services encapsulate business logic and coordinate between the MCP tools and external APIs:
- Each service handles a specific domain (e.g., TimerService, TaskService)
- Services use the client to make API calls
- Services return Pydantic models for type safety

### Adding New MCP Servers
1. Create directory under `src/app_vitals_mcp/servers/{server_name}/`
2. Follow the existing structure pattern (client, services, models, config, server, main)
3. Add entry point to `pyproject.toml` under `[project.scripts]`
4. Use FastMCP's `@mcp.tool()` decorator to expose functionality

### Configuration
- All servers use environment variables for configuration
- Config classes inherit from Pydantic BaseSettings
- Required vars are validated at startup

### Dependencies
- **FastMCP** - MCP framework for building servers
- **httpx** - Async HTTP client for API calls
- **Pydantic** - Data validation and settings management
- **uv** - Package and dependency management tool