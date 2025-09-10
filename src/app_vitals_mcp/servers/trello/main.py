#!/usr/bin/env python3
"""Trello MCP Server main entry point."""

import os

from .config import TrelloConfig
from .server import TrelloServer


def main():
    """Main entry point for the Trello MCP server."""
    # Get configuration from environment
    api_key = os.getenv("TRELLO_API_KEY")
    if not api_key:
        raise ValueError("TRELLO_API_KEY environment variable is required")
    
    token = os.getenv("TRELLO_TOKEN")
    if not token:
        raise ValueError("TRELLO_TOKEN environment variable is required")
    
    config = TrelloConfig(
        api_key=api_key,
        token=token
    )
    
    # Create and run server
    server = TrelloServer(config)
    server.mcp.run()


if __name__ == "__main__":
    main()