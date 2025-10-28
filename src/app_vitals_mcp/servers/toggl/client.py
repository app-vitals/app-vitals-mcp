"""Low-level Toggl API client."""

from datetime import datetime
from typing import List, Optional, Dict, Any

import httpx

from .models import TimeEntry, Project, Workspace, Task, Client, User, ProjectUser


class TogglClient:
    """Toggl API client."""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.track.toggl.com/api/v9"
        self.client = httpx.AsyncClient(
            auth=(api_token, "api_token"),
            headers={"Content-Type": "application/json"}
        )
    
    async def get_current_user(self) -> dict:
        """Get current user information."""
        response = await self.client.get(f"{self.base_url}/me")
        response.raise_for_status()
        return response.json()
    
    async def get_workspaces(self) -> List[Workspace]:
        """Get user workspaces."""
        response = await self.client.get(f"{self.base_url}/workspaces")
        response.raise_for_status()
        data = response.json()
        return [Workspace(**workspace) for workspace in data]
    
    async def get_projects(self, workspace_id: int) -> List[Project]:
        """Get projects for a workspace."""
        response = await self.client.get(f"{self.base_url}/workspaces/{workspace_id}/projects")
        response.raise_for_status()
        data = response.json()
        return [Project(**project) for project in data]
    
    async def get_time_entries(self, start_date: str, end_date: str) -> List[TimeEntry]:
        """Get time entries for a date range."""
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        response = await self.client.get(f"{self.base_url}/me/time_entries", params=params)
        response.raise_for_status()
        data = response.json()
        return [TimeEntry(**entry) for entry in data]
    
    async def create_time_entry(self, workspace_id: int, description: str = "", 
                               start: Optional[str] = None, duration: Optional[int] = None,
                               project_id: Optional[int] = None, task_id: Optional[int] = None,
                               tags: Optional[List[str]] = None, billable: bool = False) -> TimeEntry:
        """Create a new time entry."""
        payload: Dict[str, Any] = {
            "description": description,
            "start": start or datetime.utcnow().isoformat() + "Z",
            "created_with": "mcp-server-toggl",
            "billable": billable,
            "wid": workspace_id
        }
        
        if duration is not None:
            payload["duration"] = duration
        if project_id:
            payload["project_id"] = project_id
        if task_id:
            payload["task_id"] = task_id
        if tags:
            payload["tags"] = tags
            
        response = await self.client.post(
            f"{self.base_url}/workspaces/{workspace_id}/time_entries",
            json=payload
        )
        response.raise_for_status()
        return TimeEntry(**response.json())

    async def start_time_entry(self, description: str, project_id: Optional[int] = None, 
                              task_id: Optional[int] = None,
                              workspace_id: Optional[int] = None, tags: Optional[List[str]] = None) -> TimeEntry:
        """Start a new time entry (running timer)."""
        payload: Dict[str, Any] = {
            "description": description,
            "start": datetime.utcnow().isoformat() + "Z",
            "created_with": "mcp-server-toggl",
            "wid": workspace_id,
            "duration": -1  # Negative duration indicates running timer
        }
        
        if project_id:
            payload["project_id"] = project_id
        if task_id:
            payload["task_id"] = task_id
        if tags:
            payload["tags"] = tags
            
        response = await self.client.post(
            f"{self.base_url}/workspaces/{workspace_id}/time_entries",
            json=payload
        )
        response.raise_for_status()
        return TimeEntry(**response.json())
    
    async def update_time_entry(self, workspace_id: int, time_entry_id: int, 
                               description: Optional[str] = None, start: Optional[str] = None,
                               duration: Optional[int] = None, project_id: Optional[int] = None,
                               task_id: Optional[int] = None,
                               tags: Optional[List[str]] = None, billable: Optional[bool] = None) -> TimeEntry:
        """Update an existing time entry."""
        payload: Dict[str, Any] = {}
        
        if description is not None:
            payload["description"] = description
        if start is not None:
            payload["start"] = start
        if duration is not None:
            payload["duration"] = duration
        if project_id is not None:
            payload["project_id"] = project_id
        if task_id is not None:
            payload["task_id"] = task_id
        if tags is not None:
            payload["tags"] = tags
        if billable is not None:
            payload["billable"] = billable
            
        response = await self.client.put(
            f"{self.base_url}/workspaces/{workspace_id}/time_entries/{time_entry_id}",
            json=payload
        )
        response.raise_for_status()
        return TimeEntry(**response.json())

    async def stop_time_entry(self, workspace_id: int, time_entry_id: int) -> TimeEntry:
        """Stop a running time entry."""
        response = await self.client.patch(
            f"{self.base_url}/workspaces/{workspace_id}/time_entries/{time_entry_id}/stop"
        )
        response.raise_for_status()
        return TimeEntry(**response.json())

    async def delete_time_entry(self, workspace_id: int, time_entry_id: int) -> bool:
        """Delete a time entry."""
        response = await self.client.delete(
            f"{self.base_url}/workspaces/{workspace_id}/time_entries/{time_entry_id}"
        )
        response.raise_for_status()
        return response.status_code == 200

    async def get_time_entry(self, time_entry_id: int) -> Optional[TimeEntry]:
        """Get a specific time entry."""
        response = await self.client.get(f"{self.base_url}/me/time_entries/{time_entry_id}")
        if response.status_code == 200:
            return TimeEntry(**response.json())
        return None
    
    async def get_current_time_entry(self) -> Optional[TimeEntry]:
        """Get currently running time entry."""
        response = await self.client.get(f"{self.base_url}/me/time_entries/current")
        if response.status_code == 200:
            try:
                data = response.json()
                if data:
                    return TimeEntry(**data)
            except Exception:
                # Handle empty response or invalid JSON
                pass
        return None
    
    # Tasks API methods
    async def get_tasks(self, workspace_id: int, project_id: Optional[int] = None, 
                       active: Optional[bool] = None) -> List[Task]:
        """Get tasks for a workspace, optionally filtered by project and active status."""
        if project_id:
            # Get tasks for a specific project
            url = f"{self.base_url}/workspaces/{workspace_id}/projects/{project_id}/tasks"
        else:
            # Get all tasks in workspace (this might need different endpoint)
            url = f"{self.base_url}/workspaces/{workspace_id}/tasks"
        
        params = {}
        if active is not None:
            params["active"] = "true" if active else "false"
            
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return [Task(**task) for task in data]
    
    async def get_task(self, workspace_id: int, project_id: int, task_id: int) -> Optional[Task]:
        """Get a specific task."""
        response = await self.client.get(
            f"{self.base_url}/workspaces/{workspace_id}/projects/{project_id}/tasks/{task_id}"
        )
        if response.status_code == 200:
            return Task(**response.json())
        return None
    
    async def create_task(self, workspace_id: int, project_id: int, name: str, 
                         estimated_seconds: Optional[int] = None, active: bool = True) -> Task:
        """Create a new task."""
        payload: Dict[str, Any] = {
            "name": name,
            "active": active
        }
        if estimated_seconds is not None:
            payload["estimated_seconds"] = estimated_seconds
            
        response = await self.client.post(
            f"{self.base_url}/workspaces/{workspace_id}/projects/{project_id}/tasks",
            json=payload
        )
        response.raise_for_status()
        return Task(**response.json())
    
    async def update_task(self, workspace_id: int, project_id: int, task_id: int,
                         name: Optional[str] = None, estimated_seconds: Optional[int] = None,
                         active: Optional[bool] = None) -> Task:
        """Update an existing task."""
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if estimated_seconds is not None:
            payload["estimated_seconds"] = estimated_seconds
        if active is not None:
            payload["active"] = active
            
        response = await self.client.put(
            f"{self.base_url}/workspaces/{workspace_id}/projects/{project_id}/tasks/{task_id}",
            json=payload
        )
        response.raise_for_status()
        return Task(**response.json())
    
    async def delete_task(self, workspace_id: int, project_id: int, task_id: int) -> bool:
        """Delete a task."""
        response = await self.client.delete(
            f"{self.base_url}/workspaces/{workspace_id}/projects/{project_id}/tasks/{task_id}"
        )
        response.raise_for_status()
        return response.status_code == 200

    # Projects API methods
    async def get_project(self, workspace_id: int, project_id: int) -> Optional[Project]:
        """Get a specific project."""
        response = await self.client.get(
            f"{self.base_url}/workspaces/{workspace_id}/projects/{project_id}"
        )
        if response.status_code == 200:
            return Project(**response.json())
        return None

    async def create_project(self, workspace_id: int, name: str,
                           active: bool = True, color: str = "#3750b5",
                           client_id: Optional[int] = None,
                           billable: Optional[bool] = None,
                           is_private: bool = False) -> Project:
        """Create a new project.

        Args:
            workspace_id: The workspace ID
            name: Project name (required)
            active: Whether the project is active (default: True)
            color: Project color in hex format (default: "#3750b5")
            client_id: Optional client ID to associate with project
            billable: Whether the project is billable
            is_private: Whether the project is private (default: False)
        """
        payload: Dict[str, Any] = {
            "name": name,
            "active": active,
            "color": color,
            "is_private": is_private
        }
        if client_id is not None:
            payload["client_id"] = client_id
        if billable is not None:
            payload["billable"] = billable

        response = await self.client.post(
            f"{self.base_url}/workspaces/{workspace_id}/projects",
            json=payload
        )
        response.raise_for_status()
        return Project(**response.json())

    async def update_project(self, workspace_id: int, project_id: int,
                           name: Optional[str] = None,
                           active: Optional[bool] = None,
                           color: Optional[str] = None,
                           client_id: Optional[int] = None,
                           billable: Optional[bool] = None,
                           is_private: Optional[bool] = None) -> Project:
        """Update an existing project.

        Args:
            workspace_id: The workspace ID
            project_id: The project ID
            name: New project name
            active: Whether the project is active
            color: New project color in hex format
            client_id: New client ID (use -1 to remove client)
            billable: Whether the project is billable
            is_private: Whether the project is private
        """
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if active is not None:
            payload["active"] = active
        if color is not None:
            payload["color"] = color
        if client_id is not None:
            payload["client_id"] = client_id
        if billable is not None:
            payload["billable"] = billable
        if is_private is not None:
            payload["is_private"] = is_private

        response = await self.client.put(
            f"{self.base_url}/workspaces/{workspace_id}/projects/{project_id}",
            json=payload
        )
        response.raise_for_status()
        return Project(**response.json())

    async def delete_project(self, workspace_id: int, project_id: int) -> bool:
        """Delete a project."""
        response = await self.client.delete(
            f"{self.base_url}/workspaces/{workspace_id}/projects/{project_id}"
        )
        response.raise_for_status()
        return response.status_code == 200

    # Clients API methods
    async def get_clients(self, workspace_id: int, status: Optional[str] = None,
                         name: Optional[str] = None) -> List[Client]:
        """Get clients for a workspace.

        Args:
            workspace_id: The workspace ID
            status: Filter by status - 'active', 'archived', or 'both'
            name: Filter by name (case-insensitive match)
        """
        params = {}
        if status is not None:
            params["status"] = status
        if name is not None:
            params["name"] = name

        response = await self.client.get(
            f"{self.base_url}/workspaces/{workspace_id}/clients",
            params=params
        )
        response.raise_for_status()
        data = response.json()
        return [Client(**client) for client in data]

    async def get_client(self, workspace_id: int, client_id: int) -> Optional[Client]:
        """Get a specific client."""
        response = await self.client.get(
            f"{self.base_url}/workspaces/{workspace_id}/clients/{client_id}"
        )
        if response.status_code == 200:
            return Client(**response.json())
        return None

    async def create_client(self, workspace_id: int, name: str,
                          notes: Optional[str] = None,
                          external_reference: Optional[str] = None) -> Client:
        """Create a new client.

        Args:
            workspace_id: The workspace ID
            name: Client name (required)
            notes: Optional notes about the client
            external_reference: Optional external reference ID
        """
        payload: Dict[str, Any] = {"name": name}
        if notes is not None:
            payload["notes"] = notes
        if external_reference is not None:
            payload["external_reference"] = external_reference

        response = await self.client.post(
            f"{self.base_url}/workspaces/{workspace_id}/clients",
            json=payload
        )
        response.raise_for_status()
        return Client(**response.json())

    async def update_client(self, workspace_id: int, client_id: int,
                          name: Optional[str] = None,
                          notes: Optional[str] = None,
                          external_reference: Optional[str] = None) -> Client:
        """Update an existing client.

        Args:
            workspace_id: The workspace ID
            client_id: The client ID
            name: New client name
            notes: New notes
            external_reference: New external reference
        """
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if notes is not None:
            payload["notes"] = notes
        if external_reference is not None:
            payload["external_reference"] = external_reference

        response = await self.client.put(
            f"{self.base_url}/workspaces/{workspace_id}/clients/{client_id}",
            json=payload
        )
        response.raise_for_status()
        return Client(**response.json())

    async def delete_client(self, workspace_id: int, client_id: int) -> bool:
        """Delete a client permanently."""
        response = await self.client.delete(
            f"{self.base_url}/workspaces/{workspace_id}/clients/{client_id}"
        )
        response.raise_for_status()
        return response.status_code == 200

    async def archive_client(self, workspace_id: int, client_id: int) -> List[int]:
        """Archive a client and related projects (premium workspaces only).

        Returns:
            List of archived project IDs
        """
        response = await self.client.post(
            f"{self.base_url}/workspaces/{workspace_id}/clients/{client_id}/archive"
        )
        response.raise_for_status()
        return response.json()  # Returns array of archived project IDs

    async def restore_client(self, workspace_id: int, client_id: int,
                           restore_all_projects: bool = False,
                           project_ids: Optional[List[int]] = None) -> Client:
        """Restore an archived client.

        Args:
            workspace_id: The workspace ID
            client_id: The client ID
            restore_all_projects: If True, restore all related projects
            project_ids: List of specific project IDs to restore
        """
        payload: Dict[str, Any] = {}
        if restore_all_projects:
            payload["restore_all_projects"] = True
        elif project_ids:
            payload["project_ids"] = project_ids

        response = await self.client.post(
            f"{self.base_url}/workspaces/{workspace_id}/clients/{client_id}/restore",
            json=payload if payload else None
        )
        response.raise_for_status()
        return Client(**response.json())

    # Workspace Users API

    async def get_workspace_users(self, workspace_id: int,
                                 exclude_deleted: bool = True) -> List[User]:
        """Get all users in a workspace.

        Args:
            workspace_id: The workspace ID
            exclude_deleted: If True, exclude deleted users

        Returns:
            List of User objects
        """
        params = {}
        if exclude_deleted:
            params["exclude_deleted"] = "true"

        response = await self.client.get(
            f"{self.base_url}/workspaces/{workspace_id}/users",
            params=params if params else None
        )
        response.raise_for_status()
        return [User(**user) for user in response.json()]

    # Project Users API

    async def get_project_users(self, workspace_id: int,
                               project_ids: Optional[List[int]] = None,
                               user_id: Optional[int] = None) -> List[ProjectUser]:
        """Get project users (members) for a workspace.

        Args:
            workspace_id: The workspace ID
            project_ids: Optional list of project IDs to filter by
            user_id: Optional user ID to filter by

        Returns:
            List of ProjectUser objects
        """
        params: Dict[str, Any] = {}
        if project_ids:
            params["project_ids"] = ",".join(map(str, project_ids))
        if user_id is not None:
            params["user_id"] = str(user_id)

        response = await self.client.get(
            f"{self.base_url}/workspaces/{workspace_id}/project_users",
            params=params if params else None
        )
        response.raise_for_status()
        return [ProjectUser(**pu) for pu in response.json()]

    async def add_project_user(self, workspace_id: int, project_id: int, user_id: int,
                              manager: bool = False, rate: Optional[float] = None,
                              labor_cost: Optional[float] = None,
                              rate_change_mode: Optional[str] = None,
                              labor_cost_change_mode: Optional[str] = None) -> ProjectUser:
        """Add a user to a project.

        Args:
            workspace_id: The workspace ID
            project_id: The project ID
            user_id: The user ID to add
            manager: Whether the user should be a project manager
            rate: Hourly rate for this project user
            labor_cost: Labor cost for this project user
            rate_change_mode: "start-today", "override-current", or "override-all"
            labor_cost_change_mode: "start-today", "override-current", or "override-all"

        Returns:
            ProjectUser object
        """
        payload: Dict[str, Any] = {
            "project_id": project_id,
            "user_id": user_id,
            "manager": manager
        }

        if rate is not None:
            payload["rate"] = rate
        if labor_cost is not None:
            payload["labor_cost"] = labor_cost
        if rate_change_mode:
            payload["rate_change_mode"] = rate_change_mode
        if labor_cost_change_mode:
            payload["labor_cost_change_mode"] = labor_cost_change_mode

        response = await self.client.post(
            f"{self.base_url}/workspaces/{workspace_id}/project_users",
            json=payload
        )
        response.raise_for_status()
        return ProjectUser(**response.json())

    async def update_project_user(self, workspace_id: int, project_user_id: int,
                                 manager: Optional[bool] = None,
                                 rate: Optional[float] = None,
                                 labor_cost: Optional[float] = None,
                                 rate_change_mode: Optional[str] = None,
                                 labor_cost_change_mode: Optional[str] = None) -> ProjectUser:
        """Update a project user.

        Args:
            workspace_id: The workspace ID
            project_user_id: The project user ID
            manager: Whether the user should be a project manager
            rate: Hourly rate for this project user
            labor_cost: Labor cost for this project user
            rate_change_mode: "start-today", "override-current", or "override-all"
            labor_cost_change_mode: "start-today", "override-current", or "override-all"

        Returns:
            Updated ProjectUser object
        """
        payload: Dict[str, Any] = {}

        if manager is not None:
            payload["manager"] = manager
        if rate is not None:
            payload["rate"] = rate
        if labor_cost is not None:
            payload["labor_cost"] = labor_cost
        if rate_change_mode:
            payload["rate_change_mode"] = rate_change_mode
        if labor_cost_change_mode:
            payload["labor_cost_change_mode"] = labor_cost_change_mode

        response = await self.client.put(
            f"{self.base_url}/workspaces/{workspace_id}/project_users/{project_user_id}",
            json=payload
        )
        response.raise_for_status()
        return ProjectUser(**response.json())

    async def delete_project_user(self, workspace_id: int, project_user_id: int) -> bool:
        """Remove a user from a project.

        Args:
            workspace_id: The workspace ID
            project_user_id: The project user ID

        Returns:
            True if successful
        """
        response = await self.client.delete(
            f"{self.base_url}/workspaces/{workspace_id}/project_users/{project_user_id}"
        )
        response.raise_for_status()
        return response.status_code == 200

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()