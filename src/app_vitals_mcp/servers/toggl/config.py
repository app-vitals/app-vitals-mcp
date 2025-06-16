"""Configuration models for Toggl MCP Server."""

from typing import Optional
from pydantic import BaseModel


class TogglConfig(BaseModel):
    """Configuration for Toggl MCP Server."""
    api_token: str
    workspace_id: Optional[int] = None