"""Low-level Toggl API client."""

from datetime import datetime
from typing import List, Optional

import httpx

from .models import TimeEntry, Project, Workspace


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
                               project_id: Optional[int] = None, tags: Optional[List[str]] = None,
                               billable: bool = False) -> TimeEntry:
        """Create a new time entry."""
        payload = {
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
        if tags:
            payload["tags"] = tags
            
        response = await self.client.post(
            f"{self.base_url}/workspaces/{workspace_id}/time_entries",
            json=payload
        )
        response.raise_for_status()
        return TimeEntry(**response.json())

    async def start_time_entry(self, description: str, project_id: Optional[int] = None, 
                              workspace_id: Optional[int] = None, tags: Optional[List[str]] = None) -> TimeEntry:
        """Start a new time entry (running timer)."""
        payload = {
            "description": description,
            "start": datetime.utcnow().isoformat() + "Z",
            "created_with": "mcp-server-toggl",
            "wid": workspace_id,
            "duration": -1  # Negative duration indicates running timer
        }
        
        if project_id:
            payload["project_id"] = project_id
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
                               tags: Optional[List[str]] = None, billable: Optional[bool] = None) -> TimeEntry:
        """Update an existing time entry."""
        payload = {}
        
        if description is not None:
            payload["description"] = description
        if start is not None:
            payload["start"] = start
        if duration is not None:
            payload["duration"] = duration
        if project_id is not None:
            payload["project_id"] = project_id
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
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()