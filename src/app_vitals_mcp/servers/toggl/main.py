#!/usr/bin/env python3
"""Toggl MCP Server main entry point."""

import asyncio
import os
from typing import Optional

from fastmcp import FastMCP
from pydantic import BaseModel

from .config import TogglConfig
from .server import TogglServer


def main():
    """Main entry point for the Toggl MCP server."""
    # Get configuration from environment
    api_token = os.getenv("TOGGL_API_TOKEN")
    if not api_token:
        raise ValueError("TOGGL_API_TOKEN environment variable is required")
    
    workspace_id = os.getenv("TOGGL_WORKSPACE_ID")
    if workspace_id:
        workspace_id = int(workspace_id)
    
    config = TogglConfig(
        api_token=api_token,
        workspace_id=workspace_id
    )
    
    # Create and run server
    server = TogglServer(config)
    server.mcp.run()


if __name__ == "__main__":
    main()