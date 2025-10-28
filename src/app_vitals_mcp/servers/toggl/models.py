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
    billable: Optional[bool] = None
    is_private: bool = False


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


class User(BaseModel):
    """Toggl workspace user model."""
    id: int
    email: str
    fullname: str
    inactive: bool = False
    is_active: bool = True
    is_admin: bool = False
    role: Optional[str] = None


class Client(BaseModel):
    """Toggl client model."""
    id: int
    name: str
    wid: int  # workspace_id
    archived: bool = False
    notes: Optional[str] = None
    external_reference: Optional[str] = None
    at: Optional[str] = None  # timestamp
    creator_id: Optional[int] = None


class ProjectUser(BaseModel):
    """Toggl project user (member) model."""
    id: int
    user_id: int
    project_id: int
    workspace_id: int
    manager: bool = False
    rate: Optional[float] = None
    rate_last_updated: Optional[str] = None
    labor_cost: Optional[float] = None
    labor_cost_last_updated: Optional[str] = None
    at: Optional[str] = None  # timestamp
    gid: Optional[int] = None
    group_id: Optional[int] = None