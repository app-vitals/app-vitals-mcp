"""Service layer for Toggl MCP server."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .client import TogglClient
from .models import TimeEntry, Project, Workspace


class TimerService:
    """Service for timer-related operations."""
    
    def __init__(self, client: TogglClient, default_workspace_id: Optional[int] = None):
        self.client = client
        self.default_workspace_id = default_workspace_id
    
    async def _get_workspace_id(self) -> Optional[int]:
        """Get workspace ID, using default or fetching first available."""
        if self.default_workspace_id:
            return self.default_workspace_id
        
        workspaces = await self.client.get_workspaces()
        return workspaces[0].id if workspaces else None
    
    async def get_current_timer(self) -> Optional[TimeEntry]:
        """Get currently running timer."""
        return await self.client.get_current_time_entry()
    
    async def start_timer(self, description: str, project_id: int, 
                         tags: Optional[List[str]] = None) -> TimeEntry:
        """Start a new timer."""
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")
        
        return await self.client.start_time_entry(
            description=description,
            project_id=project_id,
            workspace_id=workspace_id,
            tags=tags
        )
    
    async def stop_current_timer(self) -> Optional[TimeEntry]:
        """Stop the currently running timer."""
        current = await self.client.get_current_time_entry()
        if not current:
            return None
        
        return await self.client.stop_time_entry(current.workspace_id, current.id)


class TimeEntryService:
    """Service for time entry CRUD operations."""
    
    def __init__(self, client: TogglClient, default_workspace_id: Optional[int] = None):
        self.client = client
        self.default_workspace_id = default_workspace_id
    
    async def _get_workspace_id(self) -> Optional[int]:
        """Get workspace ID, using default or fetching first available."""
        if self.default_workspace_id:
            return self.default_workspace_id
        
        workspaces = await self.client.get_workspaces()
        return workspaces[0].id if workspaces else None
    
    async def create_entry(self, description: str, start_time: str, duration_minutes: int,
                          project_id: int, tags: Optional[List[str]] = None,
                          billable: bool = True) -> TimeEntry:
        """Create a completed time entry."""
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")
        
        return await self.client.create_time_entry(
            workspace_id=workspace_id,
            description=description,
            start=start_time,
            duration=duration_minutes * 60,  # Convert to seconds
            project_id=project_id,
            tags=tags,
            billable=billable
        )
    
    async def get_entry(self, time_entry_id: int) -> Optional[TimeEntry]:
        """Get a specific time entry."""
        return await self.client.get_time_entry(time_entry_id)
    
    async def update_entry(self, time_entry_id: int, description: Optional[str] = None,
                          start_time: Optional[str] = None, duration_minutes: Optional[int] = None,
                          project_id: Optional[int] = None, tags: Optional[List[str]] = None,
                          billable: Optional[bool] = None) -> TimeEntry:
        """Update an existing time entry."""
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")
        
        duration_seconds = duration_minutes * 60 if duration_minutes is not None else None
        
        return await self.client.update_time_entry(
            workspace_id=workspace_id,
            time_entry_id=time_entry_id,
            description=description,
            start=start_time,
            duration=duration_seconds,
            project_id=project_id,
            tags=tags,
            billable=billable
        )
    
    async def delete_entry(self, time_entry_id: int) -> bool:
        """Delete a time entry."""
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")
        
        return await self.client.delete_time_entry(workspace_id, time_entry_id)


class AnalyticsService:
    """Service for analytics and reporting."""
    
    def __init__(self, client: TogglClient):
        self.client = client
    
    async def get_time_entries(self, days_back: int = 7) -> List[TimeEntry]:
        """Get recent time entries."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        return await self.client.get_time_entries(
            start_date.isoformat() + "Z",
            end_date.isoformat() + "Z"
        )
    
    async def get_time_summary(self, days_back: int = 7) -> Dict[str, Any]:
        """Get time tracking summary with project breakdown."""
        entries = await self.get_time_entries(days_back)
        
        total_seconds = sum(entry.duration for entry in entries if entry.duration > 0)
        total_hours = total_seconds / 3600
        
        # Group by project
        project_time = {}
        for entry in entries:
            if entry.duration > 0:
                project_id = entry.project_id or "No Project"
                if project_id not in project_time:
                    project_time[project_id] = 0
                project_time[project_id] += entry.duration
        
        return {
            "total_hours": round(total_hours, 2),
            "total_entries": len(entries),
            "project_breakdown": {
                str(k): round(v / 3600, 2) for k, v in project_time.items()
            },
            "period_days": days_back
        }


class WorkspaceService:
    """Service for workspace and project management."""
    
    def __init__(self, client: TogglClient):
        self.client = client
    
    async def get_workspaces(self) -> List[Workspace]:
        """Get available workspaces."""
        return await self.client.get_workspaces()
    
    async def get_projects(self, workspace_id: Optional[int] = None) -> List[Project]:
        """Get projects for a workspace."""
        if not workspace_id:
            workspaces = await self.client.get_workspaces()
            workspace_id = workspaces[0].id if workspaces else None
        
        if not workspace_id:
            return []
        
        return await self.client.get_projects(workspace_id)