# Toggl MCP Server

A FastMCP server for integrating with Toggl time tracking API.

## Features

**Timer Operations:**
- Start and stop time entries
- Get current running time entry

**Time Entry Management:**
- Create completed time entries with custom start time and duration
- Update existing time entries (description, duration, tags, etc.)
- Delete time entries
- Retrieve specific time entries by ID

**Task Management:**
- Create and manage tasks within projects
- Track task estimates and progress
- Organize time entries by task for better invoice grouping
- Mark tasks as active/inactive

**Analytics & Reporting:**
- Get time entries for specified date ranges
- Get time tracking summaries with project breakdown

**Workspace Management:**
- Manage workspaces and projects
- Built-in rate limiting compliance

## Architecture

The server uses a clean layered architecture:
- **Client Layer** (`client.py`): Low-level Toggl API calls
- **Service Layer** (`services.py`): Business logic organized by domain
- **Server Layer** (`server.py`): MCP tool definitions and routing
- **Models** (`models.py`): Data models and validation

## Installation

Install the package:
```bash
pip install app-vitals-mcp
```

## Setup

1. Get your Toggl API token from https://track.toggl.com/profile
2. Create at least one project in your Toggl workspace (required for time entries)
3. Create at least one task within your project (required for time entries)
4. Set environment variables:
   ```bash
   export TOGGL_API_TOKEN=your_api_token_here
   export TOGGL_WORKSPACE_ID=your_workspace_id  # optional
   ```

## Usage

### Direct Usage
Run the server directly:
```bash
mcp-server-toggl
```

### MCP Client Configuration
Add to your MCP client configuration (e.g., Claude Desktop):
```json
{
  "mcp_servers": {
    "toggl": {
      "command": "mcp-server-toggl",
      "env": {
        "TOGGL_API_TOKEN": "your_api_token_here",
        "TOGGL_WORKSPACE_ID": "your_workspace_id"
      }
    }
  }
}
```

## Available Tools

### Time Entry Management
- `start_timer(description, project_id, task_id, tags=None)` - Start a new time entry (project_id and task_id required)
- `stop_timer()` - Stop the currently running time entry  
- `get_current_time_entry()` - Get the currently running time entry
- `create_time_entry(description, start_time, duration_minutes, project_id, task_id, tags=None, billable=True)` - Create a completed time entry (project_id and task_id required, billable=True by default)
- `update_time_entry(time_entry_id, description=None, start_time=None, duration_minutes=None, project_id=None, task_id=None, tags=None, billable=None)` - Update an existing time entry
- `delete_time_entry(time_entry_id)` - Delete a time entry
- `get_time_entry(time_entry_id)` - Get details of a specific time entry

### Task Management
- `get_tasks(project_id=None, active=None)` - Get tasks, optionally filtered by project and active status
- `get_task(project_id, task_id)` - Get details of a specific task
- `create_task(project_id, name, estimated_hours=None, active=True)` - Create a new task in a project
- `update_task(project_id, task_id, name=None, estimated_hours=None, active=None)` - Update an existing task
- `delete_task(project_id, task_id)` - Delete a task

### Data Retrieval
- `get_time_entries(days_back=7)` - Get recent time entries
- `get_time_summary(days_back=7)` - Get time tracking summary with project breakdown
- `get_workspaces()` - Get available workspaces
- `get_projects(workspace_id=None)` - Get projects for a workspace

## Configuration

Required environment variables:
- `TOGGL_API_TOKEN` - Your Toggl API token

Optional environment variables:
- `TOGGL_WORKSPACE_ID` - Default workspace ID (will use first workspace if not set)

## API Compliance

This server follows Toggl API v9 best practices:
- Rate limiting (approximately 1 request per second)
- Proper error handling for 4xx/5xx responses
- UTC time handling
- JSON-only requests
- Eventual consistency handling