"""Service layer for Toggl MCP server."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .client import TogglClient
from .models import TimeEntry, Project, Workspace, Task, Client


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
    
    async def start_timer(self, description: str, project_id: int, task_id: int,
                         tags: Optional[List[str]] = None) -> TimeEntry:
        """Start a new timer."""
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")
        
        return await self.client.start_time_entry(
            description=description,
            project_id=project_id,
            task_id=task_id,
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
                          project_id: int, task_id: int,
                          tags: Optional[List[str]] = None,
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
            task_id=task_id,
            tags=tags,
            billable=billable
        )
    
    async def get_entry(self, time_entry_id: int) -> Optional[TimeEntry]:
        """Get a specific time entry."""
        return await self.client.get_time_entry(time_entry_id)
    
    async def update_entry(self, time_entry_id: int, description: Optional[str] = None,
                          start_time: Optional[str] = None, duration_minutes: Optional[int] = None,
                          project_id: Optional[int] = None, task_id: Optional[int] = None,
                          tags: Optional[List[str]] = None,
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
            task_id=task_id,
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


class TaskService:
    """Service for task management."""
    
    def __init__(self, client: TogglClient, workspace_id: Optional[int] = None):
        self.client = client
        self.default_workspace_id = workspace_id
    
    async def _get_workspace_id(self) -> Optional[int]:
        """Get workspace ID (from config or first available)."""
        if self.default_workspace_id:
            return self.default_workspace_id
        
        workspaces = await self.client.get_workspaces()
        return workspaces[0].id if workspaces else None
    
    async def get_tasks(self, project_id: Optional[int] = None, 
                       active: Optional[bool] = None) -> List[Task]:
        """Get tasks, optionally filtered by project and active status."""
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")
        
        return await self.client.get_tasks(workspace_id, project_id, active)
    
    async def get_task(self, project_id: int, task_id: int) -> Optional[Task]:
        """Get a specific task."""
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")
        
        return await self.client.get_task(workspace_id, project_id, task_id)
    
    async def create_task(self, project_id: int, name: str, 
                         estimated_seconds: Optional[int] = None, 
                         active: bool = True) -> Task:
        """Create a new task."""
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")
        
        return await self.client.create_task(
            workspace_id, project_id, name, estimated_seconds, active
        )
    
    async def update_task(self, project_id: int, task_id: int,
                         name: Optional[str] = None, 
                         estimated_seconds: Optional[int] = None,
                         active: Optional[bool] = None) -> Task:
        """Update an existing task."""
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")
        
        return await self.client.update_task(
            workspace_id, project_id, task_id, name, estimated_seconds, active
        )
    
    async def delete_task(self, project_id: int, task_id: int) -> bool:
        """Delete a task."""
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")

        return await self.client.delete_task(workspace_id, project_id, task_id)


class ProjectService:
    """Service for project management."""

    def __init__(self, client: TogglClient, workspace_id: Optional[int] = None):
        self.client = client
        self.default_workspace_id = workspace_id

    async def _get_workspace_id(self) -> Optional[int]:
        """Get workspace ID (from config or first available)."""
        if self.default_workspace_id:
            return self.default_workspace_id

        workspaces = await self.client.get_workspaces()
        return workspaces[0].id if workspaces else None

    async def get_projects(self, workspace_id: Optional[int] = None) -> List[Project]:
        """Get all projects for a workspace."""
        if workspace_id is None:
            workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")

        return await self.client.get_projects(workspace_id)

    async def get_project(self, project_id: int) -> Optional[Project]:
        """Get a specific project."""
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")

        return await self.client.get_project(workspace_id, project_id)

    async def create_project(self, name: str, active: bool = True,
                           color: str = "#3750b5", client_id: Optional[int] = None,
                           billable: Optional[bool] = None,
                           is_private: bool = False) -> Project:
        """Create a new project.

        Args:
            name: Project name (required)
            active: Whether the project is active (default: True)
            color: Project color in hex format (default: "#3750b5")
            client_id: Optional client ID to associate with project
            billable: Whether the project is billable
            is_private: Whether the project is private (default: False)
        """
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")

        return await self.client.create_project(
            workspace_id, name, active, color, client_id, billable, is_private
        )

    async def update_project(self, project_id: int, name: Optional[str] = None,
                           active: Optional[bool] = None, color: Optional[str] = None,
                           client_id: Optional[int] = None,
                           billable: Optional[bool] = None,
                           is_private: Optional[bool] = None) -> Project:
        """Update an existing project.

        Args:
            project_id: The project ID
            name: New project name
            active: Whether the project is active
            color: New project color in hex format
            client_id: New client ID (use -1 to remove client)
            billable: Whether the project is billable
            is_private: Whether the project is private
        """
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")

        return await self.client.update_project(
            workspace_id, project_id, name, active, color, client_id, billable, is_private
        )

    async def delete_project(self, project_id: int) -> bool:
        """Delete a project."""
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")

        return await self.client.delete_project(workspace_id, project_id)


class ClientService:
    """Service for client management."""

    def __init__(self, client: TogglClient, workspace_id: Optional[int] = None):
        self.client = client
        self.default_workspace_id = workspace_id

    async def _get_workspace_id(self) -> Optional[int]:
        """Get workspace ID (from config or first available)."""
        if self.default_workspace_id:
            return self.default_workspace_id

        workspaces = await self.client.get_workspaces()
        return workspaces[0].id if workspaces else None

    async def get_clients(self, status: Optional[str] = None,
                         name: Optional[str] = None) -> List[Client]:
        """Get clients, optionally filtered by status and name.

        Args:
            status: Filter by status - 'active', 'archived', or 'both'
            name: Filter by name (case-insensitive match)
        """
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")

        return await self.client.get_clients(workspace_id, status, name)

    async def get_client(self, client_id: int) -> Optional[Client]:
        """Get a specific client."""
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")

        return await self.client.get_client(workspace_id, client_id)

    async def create_client(self, name: str, notes: Optional[str] = None,
                          external_reference: Optional[str] = None) -> Client:
        """Create a new client.

        Args:
            name: Client name (required)
            notes: Optional notes about the client
            external_reference: Optional external reference ID
        """
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")

        return await self.client.create_client(
            workspace_id, name, notes, external_reference
        )

    async def update_client(self, client_id: int, name: Optional[str] = None,
                          notes: Optional[str] = None,
                          external_reference: Optional[str] = None) -> Client:
        """Update an existing client.

        Args:
            client_id: The client ID
            name: New client name
            notes: New notes
            external_reference: New external reference
        """
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")

        return await self.client.update_client(
            workspace_id, client_id, name, notes, external_reference
        )

    async def delete_client(self, client_id: int) -> bool:
        """Delete a client permanently."""
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")

        return await self.client.delete_client(workspace_id, client_id)

    async def archive_client(self, client_id: int) -> List[int]:
        """Archive a client and related projects (premium workspaces only).

        Returns:
            List of archived project IDs
        """
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")

        return await self.client.archive_client(workspace_id, client_id)

    async def restore_client(self, client_id: int,
                           restore_all_projects: bool = False,
                           project_ids: Optional[List[int]] = None) -> Client:
        """Restore an archived client.

        Args:
            client_id: The client ID
            restore_all_projects: If True, restore all related projects
            project_ids: List of specific project IDs to restore
        """
        workspace_id = await self._get_workspace_id()
        if not workspace_id:
            raise ValueError("No workspace available")

        return await self.client.restore_client(
            workspace_id, client_id, restore_all_projects, project_ids
        )