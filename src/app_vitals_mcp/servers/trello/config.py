"""Configuration models for Trello MCP Server."""

from pydantic import BaseModel


class TrelloConfig(BaseModel):
    """Configuration for Trello MCP Server."""
    api_key: str
    token: str