"""Unit tests for TogglClient."""

import pytest
import respx
import httpx
from datetime import datetime, timedelta

from app_vitals_mcp.servers.toggl.client import TogglClient
from app_vitals_mcp.servers.toggl.models import TimeEntry, Project, Workspace


@pytest.mark.unit
@pytest.mark.asyncio
class TestTogglClient:
    """Test TogglClient with mocked HTTP responses."""

    @respx.mock
    async def test_get_current_user(self, mock_toggl_client: TogglClient):
        """Test getting current user information."""
        mock_response = {
            "id": 123,
            "email": "test@example.com",
            "fullname": "Test User"
        }
        
        respx.get("https://api.track.toggl.com/api/v9/me").respond(
            status_code=200,
            json=mock_response
        )
        
        result = await mock_toggl_client.get_current_user()
        assert result == mock_response

    @respx.mock
    async def test_get_workspaces(self, mock_toggl_client: TogglClient):
        """Test getting workspaces."""
        mock_response = [
            {
                "id": 12345,
                "name": "Test Workspace",
                "organization_id": 67890
            }
        ]
        
        respx.get("https://api.track.toggl.com/api/v9/workspaces").respond(
            status_code=200,
            json=mock_response
        )
        
        result = await mock_toggl_client.get_workspaces()
        assert len(result) == 1
        assert isinstance(result[0], Workspace)
        assert result[0].id == 12345
        assert result[0].name == "Test Workspace"

    @respx.mock
    async def test_get_projects(self, mock_toggl_client: TogglClient):
        """Test getting projects for a workspace."""
        workspace_id = 12345
        mock_response = [
            {
                "id": 111,
                "name": "Test Project",
                "workspace_id": workspace_id,
                "client_id": None,
                "active": True,
                "color": "#3750b5"
            }
        ]
        
        respx.get(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/projects").respond(
            status_code=200,
            json=mock_response
        )
        
        result = await mock_toggl_client.get_projects(workspace_id)
        assert len(result) == 1
        assert isinstance(result[0], Project)
        assert result[0].id == 111
        assert result[0].name == "Test Project"

    @respx.mock
    async def test_get_time_entries(self, mock_toggl_client: TogglClient):
        """Test getting time entries for a date range."""
        mock_response = [
            {
                "id": 999,
                "description": "Test task",
                "start": "2024-01-01T10:00:00Z",
                "stop": "2024-01-01T11:00:00Z",
                "duration": 3600,
                "project_id": 111,
                "workspace_id": 12345,
                "tags": ["testing"]
            }
        ]
        
        respx.get("https://api.track.toggl.com/api/v9/me/time_entries").respond(
            status_code=200,
            json=mock_response
        )
        
        start_date = "2024-01-01T00:00:00Z"
        end_date = "2024-01-02T00:00:00Z"
        result = await mock_toggl_client.get_time_entries(start_date, end_date)
        
        assert len(result) == 1
        assert isinstance(result[0], TimeEntry)
        assert result[0].id == 999
        assert result[0].description == "Test task"
        assert result[0].duration == 3600

    @respx.mock
    async def test_start_time_entry(self, mock_toggl_client: TogglClient):
        """Test starting a new time entry."""
        workspace_id = 12345
        mock_response = {
            "id": 888,
            "description": "New task",
            "start": "2024-01-01T12:00:00Z",
            "stop": None,
            "duration": -1,
            "project_id": 111,
            "workspace_id": workspace_id,
            "tags": []
        }
        
        respx.post(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/time_entries").respond(
            status_code=200,
            json=mock_response
        )
        
        result = await mock_toggl_client.start_time_entry(
            description="New task",
            project_id=111,
            workspace_id=workspace_id
        )
        
        assert isinstance(result, TimeEntry)
        assert result.id == 888
        assert result.description == "New task"
        assert result.duration == -1  # Running entry

    @respx.mock
    async def test_stop_time_entry(self, mock_toggl_client: TogglClient):
        """Test stopping a time entry."""
        workspace_id = 12345
        time_entry_id = 888
        mock_response = {
            "id": time_entry_id,
            "description": "Stopped task",
            "start": "2024-01-01T12:00:00Z",
            "stop": "2024-01-01T13:00:00Z",
            "duration": 3600,
            "project_id": 111,
            "workspace_id": workspace_id,
            "tags": []
        }
        
        respx.patch(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/time_entries/{time_entry_id}/stop").respond(
            status_code=200,
            json=mock_response
        )
        
        result = await mock_toggl_client.stop_time_entry(workspace_id, time_entry_id)
        
        assert isinstance(result, TimeEntry)
        assert result.id == time_entry_id
        assert result.duration == 3600  # Stopped entry

    @respx.mock
    async def test_get_current_time_entry_running(self, mock_toggl_client: TogglClient):
        """Test getting current time entry when one is running."""
        mock_response = {
            "id": 777,
            "description": "Current task",
            "start": "2024-01-01T14:00:00Z",
            "stop": None,
            "duration": -1,
            "project_id": 111,
            "workspace_id": 12345,
            "tags": []
        }
        
        respx.get("https://api.track.toggl.com/api/v9/me/time_entries/current").respond(
            status_code=200,
            json=mock_response
        )
        
        result = await mock_toggl_client.get_current_time_entry()
        
        assert result is not None
        assert isinstance(result, TimeEntry)
        assert result.id == 777
        assert result.duration == -1

    @respx.mock
    async def test_get_current_time_entry_none(self, mock_toggl_client: TogglClient):
        """Test getting current time entry when none is running."""
        respx.get("https://api.track.toggl.com/api/v9/me/time_entries/current").respond(
            status_code=200,
            content=""
        )
        
        result = await mock_toggl_client.get_current_time_entry()
        assert result is None

    @respx.mock
    async def test_api_error_handling(self, mock_toggl_client: TogglClient):
        """Test API error handling."""
        respx.get("https://api.track.toggl.com/api/v9/me").respond(
            status_code=401,
            json={"error": "Unauthorized"}
        )
        
        with pytest.raises(httpx.HTTPStatusError):
            await mock_toggl_client.get_current_user()

    @respx.mock
    async def test_rate_limiting_handling(self, mock_toggl_client: TogglClient):
        """Test rate limiting response handling."""
        respx.get("https://api.track.toggl.com/api/v9/me").respond(
            status_code=429,
            headers={"Retry-After": "60"},
            json={"error": "Too Many Requests"}
        )
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await mock_toggl_client.get_current_user()
        
        assert exc_info.value.response.status_code == 429

    @respx.mock
    async def test_create_time_entry(self, mock_toggl_client: TogglClient):
        """Test creating a completed time entry."""
        workspace_id = 12345
        mock_response = {
            "id": 888,
            "description": "Created task",
            "start": "2024-01-01T10:00:00Z",
            "stop": "2024-01-01T11:00:00Z",
            "duration": 3600,
            "workspace_id": workspace_id,
            "project_id": 222,
            "tags": ["test"],
            "billable": True
        }
        
        respx.post(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/time_entries").respond(
            status_code=200,
            json=mock_response
        )
        
        result = await mock_toggl_client.create_time_entry(
            workspace_id=workspace_id,
            description="Created task",
            start="2024-01-01T10:00:00Z",
            duration=3600,
            project_id=222,
            tags=["test"],
            billable=True
        )
        
        assert result.id == 888
        assert result.description == "Created task"
        assert result.billable == True

    @respx.mock
    async def test_update_time_entry(self, mock_toggl_client: TogglClient):
        """Test updating an existing time entry."""
        workspace_id = 12345
        time_entry_id = 999
        mock_response = {
            "id": time_entry_id,
            "description": "Updated task",
            "start": "2024-01-01T10:00:00Z",
            "stop": "2024-01-01T12:00:00Z",
            "duration": 7200,
            "workspace_id": workspace_id,
            "tags": ["updated"],
            "billable": False
        }
        
        respx.put(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/time_entries/{time_entry_id}").respond(
            status_code=200,
            json=mock_response
        )
        
        result = await mock_toggl_client.update_time_entry(
            workspace_id=workspace_id,
            time_entry_id=time_entry_id,
            description="Updated task",
            duration=7200,
            tags=["updated"],
            billable=False
        )
        
        assert result.id == time_entry_id
        assert result.description == "Updated task"
        assert result.duration == 7200

    @respx.mock
    async def test_delete_time_entry(self, mock_toggl_client: TogglClient):
        """Test deleting a time entry."""
        workspace_id = 12345
        time_entry_id = 777
        
        respx.delete(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/time_entries/{time_entry_id}").respond(
            status_code=200
        )
        
        result = await mock_toggl_client.delete_time_entry(workspace_id, time_entry_id)
        assert result == True

    @respx.mock
    async def test_get_time_entry(self, mock_toggl_client: TogglClient):
        """Test getting a specific time entry."""
        time_entry_id = 555
        mock_response = {
            "id": time_entry_id,
            "description": "Retrieved task",
            "start": "2024-01-01T16:00:00Z",
            "stop": "2024-01-01T17:00:00Z",
            "duration": 3600,
            "workspace_id": 12345,
            "tags": ["test"]
        }
        
        respx.get(f"https://api.track.toggl.com/api/v9/me/time_entries/{time_entry_id}").respond(
            status_code=200,
            json=mock_response
        )
        
        result = await mock_toggl_client.get_time_entry(time_entry_id)
        
        assert result is not None
        assert result.id == time_entry_id
        assert result.description == "Retrieved task"