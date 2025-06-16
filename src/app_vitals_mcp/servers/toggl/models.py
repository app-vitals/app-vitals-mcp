"""Data models for Toggl MCP server."""

from typing import List, Optional
from pydantic import BaseModel


class TimeEntry(BaseModel):
    """Toggl time entry model."""
    id: int
    description: Optional[str] = None
    start: str
    stop: Optional[str] = None
    duration: int
    project_id: Optional[int] = None
    task_id: Optional[int] = None
    workspace_id: int
    tags: Optional[List[str]] = []
    billable: Optional[bool] = False
    
    def model_post_init(self, __context):
        """Handle None tags from API."""
        if self.tags is None:
            self.tags = []


class Project(BaseModel):
    """Toggl project model."""
    id: int
    name: str
    workspace_id: int
    client_id: Optional[int] = None
    active: bool = True
    color: str = "#3750b5"


class Task(BaseModel):
    """Toggl task model."""
    id: int
    name: str
    project_id: int
    workspace_id: int
    active: bool = True
    estimated_seconds: Optional[int] = None
    tracked_seconds: Optional[int] = None


class Workspace(BaseModel):
    """Toggl workspace model."""
    id: int
    name: str
    organization_id: int