"""Toggl MCP Server implementation with layered architecture."""

from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .config import TogglConfig
from .client import TogglClient
from .services import TimerService, TimeEntryService, AnalyticsService, WorkspaceService, TaskService


class TogglServer:
    """Toggl MCP Server with layered architecture."""
    
    def __init__(self, config: TogglConfig):
        self.config = config
        self.client = TogglClient(config.api_token)
        self.mcp = FastMCP("Toggl Time Tracking Server")
        
        # Initialize services
        self.timer_service = TimerService(self.client, config.workspace_id)
        self.entry_service = TimeEntryService(self.client, config.workspace_id)
        self.analytics_service = AnalyticsService(self.client)
        self.workspace_service = WorkspaceService(self.client)
        self.task_service = TaskService(self.client, config.workspace_id)
        
        self._setup_tools()
    
    def _setup_tools(self):
        """Set up MCP tools organized by category."""
        self._setup_timer_tools()
        self._setup_entry_tools()
        self._setup_analytics_tools()
        self._setup_workspace_tools()
        self._setup_task_tools()
    
    def _setup_timer_tools(self):
        """Set up timer-related tools."""
        
        @self.mcp.tool()
        async def get_current_time_entry() -> Dict[str, Any]:
            """Get the currently running time entry."""
            entry = await self.timer_service.get_current_timer()
            if entry:
                return entry.model_dump()
            return {"status": "No time entry currently running"}
        
        @self.mcp.tool()
        async def start_timer(description: str, project_id: int, task_id: int,
                             tags: Optional[List[str]] = None) -> Dict[str, Any]:
            """Start a new time entry.
            
            Args:
                description: Description of what you're working on
                project_id: Project ID to associate with the time entry (required)
                task_id: Task ID to associate with the time entry (required)
                tags: Optional list of tags for the time entry
            """
            try:
                entry = await self.timer_service.start_timer(description, project_id, task_id, tags)
                return entry.model_dump()
            except ValueError as e:
                return {"error": str(e)}
        
        @self.mcp.tool()
        async def stop_timer() -> Dict[str, Any]:
            """Stop the currently running time entry."""
            entry = await self.timer_service.stop_current_timer()
            if entry:
                return entry.model_dump()
            return {"status": "No time entry currently running"}
    
    def _setup_entry_tools(self):
        """Set up time entry CRUD tools."""
        
        @self.mcp.tool()
        async def create_time_entry(description: str, start_time: str, duration_minutes: int,
                                   project_id: int, task_id: int,
                                   tags: Optional[List[str]] = None,
                                   billable: bool = True) -> Dict[str, Any]:
            """Create a completed time entry (not a running timer).
            
            Args:
                description: Description of what was worked on
                start_time: Start time in ISO format (e.g., "2024-01-01T10:00:00Z")
                duration_minutes: Duration in minutes
                project_id: Project ID to associate with the time entry (required)
                task_id: Task ID to associate with the time entry (required)
                tags: Optional list of tags for the time entry
                billable: Whether the time entry is billable (default: True)
            """
            try:
                entry = await self.entry_service.create_entry(
                    description, start_time, duration_minutes, project_id, task_id, tags, billable
                )
                return entry.model_dump()
            except ValueError as e:
                return {"error": str(e)}
        
        @self.mcp.tool()
        async def get_time_entry(time_entry_id: int) -> Dict[str, Any]:
            """Get details of a specific time entry.
            
            Args:
                time_entry_id: ID of the time entry to retrieve
            """
            entry = await self.entry_service.get_entry(time_entry_id)
            if entry:
                return entry.model_dump()
            return {"error": "Time entry not found"}
        
        @self.mcp.tool()
        async def update_time_entry(time_entry_id: int, description: Optional[str] = None,
                                   start_time: Optional[str] = None, duration_minutes: Optional[int] = None,
                                   project_id: Optional[int] = None, task_id: Optional[int] = None,
                                   tags: Optional[List[str]] = None,
                                   billable: Optional[bool] = None) -> Dict[str, Any]:
            """Update an existing time entry.
            
            Args:
                time_entry_id: ID of the time entry to update
                description: New description (optional)
                start_time: New start time in ISO format (optional)
                duration_minutes: New duration in minutes (optional)
                project_id: New project ID (optional)
                task_id: New task ID (optional)
                tags: New list of tags (optional)
                billable: Whether the time entry is billable (optional)
            """
            try:
                entry = await self.entry_service.update_entry(
                    time_entry_id, description, start_time, duration_minutes, 
                    project_id, task_id, tags, billable
                )
                return entry.model_dump()
            except ValueError as e:
                return {"error": str(e)}
        
        @self.mcp.tool()
        async def delete_time_entry(time_entry_id: int) -> Dict[str, Any]:
            """Delete a time entry.
            
            Args:
                time_entry_id: ID of the time entry to delete
            """
            try:
                success = await self.entry_service.delete_entry(time_entry_id)
                return {
                    "success": success,
                    "message": "Time entry deleted" if success else "Failed to delete time entry"
                }
            except ValueError as e:
                return {"error": str(e)}
    
    def _setup_analytics_tools(self):
        """Set up analytics and reporting tools."""
        
        @self.mcp.tool()
        async def get_time_entries(days_back: int = 7) -> List[Dict[str, Any]]:
            """Get recent time entries.
            
            Args:
                days_back: Number of days back to fetch entries (default: 7)
            """
            entries = await self.analytics_service.get_time_entries(days_back)
            return [entry.model_dump() for entry in entries]
        
        @self.mcp.tool()
        async def get_time_summary(days_back: int = 7) -> Dict[str, Any]:
            """Get a summary of time tracked in recent days.
            
            Args:
                days_back: Number of days back to analyze (default: 7)
            """
            return await self.analytics_service.get_time_summary(days_back)
    
    def _setup_workspace_tools(self):
        """Set up workspace and project management tools."""
        
        @self.mcp.tool()
        async def get_workspaces() -> List[Dict[str, Any]]:
            """Get available workspaces."""
            workspaces = await self.workspace_service.get_workspaces()
            return [workspace.model_dump() for workspace in workspaces]
        
        @self.mcp.tool()
        async def get_projects(workspace_id: Optional[int] = None) -> List[Dict[str, Any]]:
            """Get projects for a workspace.
            
            Args:
                workspace_id: Workspace ID (uses default if not provided)
            """
            projects = await self.workspace_service.get_projects(workspace_id)
            return [project.model_dump() for project in projects]
    
    def _setup_task_tools(self):
        """Set up task management tools."""
        
        @self.mcp.tool()
        async def get_tasks(project_id: Optional[int] = None, 
                           active: Optional[bool] = None) -> List[Dict[str, Any]]:
            """Get tasks, optionally filtered by project and active status.
            
            Args:
                project_id: Optional project ID to filter tasks
                active: Optional filter for active/inactive tasks
            """
            try:
                tasks = await self.task_service.get_tasks(project_id, active)
                return [task.model_dump() for task in tasks]
            except ValueError as e:
                return {"error": str(e)}
        
        @self.mcp.tool()
        async def get_task(project_id: int, task_id: int) -> Dict[str, Any]:
            """Get details of a specific task.
            
            Args:
                project_id: Project ID the task belongs to
                task_id: ID of the task to retrieve
            """
            task = await self.task_service.get_task(project_id, task_id)
            if task:
                return task.model_dump()
            return {"error": "Task not found"}
        
        @self.mcp.tool()
        async def create_task(project_id: int, name: str, 
                             estimated_hours: Optional[float] = None,
                             active: bool = True) -> Dict[str, Any]:
            """Create a new task in a project.
            
            Args:
                project_id: Project ID to create the task in (required)
                name: Name/description of the task
                estimated_hours: Optional estimated time in hours
                active: Whether the task is active (default: True)
            """
            try:
                estimated_seconds = None
                if estimated_hours is not None:
                    estimated_seconds = int(estimated_hours * 3600)
                
                task = await self.task_service.create_task(
                    project_id, name, estimated_seconds, active
                )
                return task.model_dump()
            except ValueError as e:
                return {"error": str(e)}
        
        @self.mcp.tool()
        async def update_task(project_id: int, task_id: int,
                             name: Optional[str] = None,
                             estimated_hours: Optional[float] = None,
                             active: Optional[bool] = None) -> Dict[str, Any]:
            """Update an existing task.
            
            Args:
                project_id: Project ID the task belongs to
                task_id: ID of the task to update
                name: New name for the task (optional)
                estimated_hours: New estimated time in hours (optional)
                active: Whether the task is active (optional)
            """
            try:
                estimated_seconds = None
                if estimated_hours is not None:
                    estimated_seconds = int(estimated_hours * 3600)
                
                task = await self.task_service.update_task(
                    project_id, task_id, name, estimated_seconds, active
                )
                return task.model_dump()
            except ValueError as e:
                return {"error": str(e)}
        
        @self.mcp.tool()
        async def delete_task(project_id: int, task_id: int) -> Dict[str, Any]:
            """Delete a task.
            
            Args:
                project_id: Project ID the task belongs to
                task_id: ID of the task to delete
            """
            try:
                success = await self.task_service.delete_task(project_id, task_id)
                if success:
                    return {"success": True, "message": f"Task {task_id} deleted successfully"}
                return {"success": False, "message": f"Failed to delete task {task_id}"}
            except ValueError as e:
                return {"error": str(e)}
    
    def run(self):
        """Run the MCP server."""
        self.mcp.run()