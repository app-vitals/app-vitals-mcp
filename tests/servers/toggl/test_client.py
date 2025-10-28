"""Unit tests for TogglClient."""

import pytest
import respx
import httpx

from app_vitals_mcp.servers.toggl.client import TogglClient
from app_vitals_mcp.servers.toggl.models import TimeEntry, Project, Workspace, Task, Client


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
            task_id=1001,
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
            task_id=1002,
            tags=["test"],
            billable=True
        )
        
        assert result.id == 888
        assert result.description == "Created task"
        assert result.billable

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
            task_id=1003,
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
        assert result

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

    @respx.mock
    async def test_get_tasks(self, mock_toggl_client: TogglClient):
        """Test getting tasks for a project."""
        workspace_id = 12345
        project_id = 111
        mock_response = [
            {
                "id": 1001,
                "name": "Design mockups",
                "project_id": project_id,
                "workspace_id": workspace_id,
                "active": True,
                "estimated_seconds": 7200,
                "tracked_seconds": 3600
            },
            {
                "id": 1002,
                "name": "Code review",
                "project_id": project_id,
                "workspace_id": workspace_id,
                "active": True,
                "estimated_seconds": None,
                "tracked_seconds": 1800
            }
        ]
        
        respx.get(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/projects/{project_id}/tasks").respond(
            status_code=200,
            json=mock_response
        )
        
        result = await mock_toggl_client.get_tasks(workspace_id, project_id)
        
        assert len(result) == 2
        assert isinstance(result[0], Task)
        assert result[0].id == 1001
        assert result[0].name == "Design mockups"
        assert result[0].estimated_seconds == 7200

    @respx.mock
    async def test_get_task(self, mock_toggl_client: TogglClient):
        """Test getting a specific task."""
        workspace_id = 12345
        project_id = 111
        task_id = 1001
        mock_response = {
            "id": task_id,
            "name": "Design mockups",
            "project_id": project_id,
            "workspace_id": workspace_id,
            "active": True,
            "estimated_seconds": 7200,
            "tracked_seconds": 3600
        }
        
        respx.get(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/projects/{project_id}/tasks/{task_id}").respond(
            status_code=200,
            json=mock_response
        )
        
        result = await mock_toggl_client.get_task(workspace_id, project_id, task_id)
        
        assert result is not None
        assert isinstance(result, Task)
        assert result.id == task_id
        assert result.name == "Design mockups"

    @respx.mock
    async def test_create_task(self, mock_toggl_client: TogglClient):
        """Test creating a new task."""
        workspace_id = 12345
        project_id = 111
        mock_response = {
            "id": 1003,
            "name": "New feature implementation",
            "project_id": project_id,
            "workspace_id": workspace_id,
            "active": True,
            "estimated_seconds": 14400,
            "tracked_seconds": 0
        }
        
        respx.post(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/projects/{project_id}/tasks").respond(
            status_code=200,
            json=mock_response
        )
        
        result = await mock_toggl_client.create_task(
            workspace_id=workspace_id,
            project_id=project_id,
            name="New feature implementation",
            estimated_seconds=14400
        )
        
        assert result.id == 1003
        assert result.name == "New feature implementation"
        assert result.estimated_seconds == 14400

    @respx.mock
    async def test_update_task(self, mock_toggl_client: TogglClient):
        """Test updating an existing task."""
        workspace_id = 12345
        project_id = 111
        task_id = 1001
        mock_response = {
            "id": task_id,
            "name": "Updated task name",
            "project_id": project_id,
            "workspace_id": workspace_id,
            "active": False,
            "estimated_seconds": 10800,
            "tracked_seconds": 3600
        }
        
        respx.put(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/projects/{project_id}/tasks/{task_id}").respond(
            status_code=200,
            json=mock_response
        )
        
        result = await mock_toggl_client.update_task(
            workspace_id=workspace_id,
            project_id=project_id,
            task_id=task_id,
            name="Updated task name",
            estimated_seconds=10800,
            active=False
        )
        
        assert result.id == task_id
        assert result.name == "Updated task name"
        assert not result.active
        assert result.estimated_seconds == 10800

    @respx.mock
    async def test_delete_task(self, mock_toggl_client: TogglClient):
        """Test deleting a task."""
        workspace_id = 12345
        project_id = 111
        task_id = 1001
        
        respx.delete(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/projects/{project_id}/tasks/{task_id}").respond(
            status_code=200
        )
        
        result = await mock_toggl_client.delete_task(workspace_id, project_id, task_id)
        assert result

    @respx.mock
    async def test_get_clients(self, mock_toggl_client: TogglClient):
        """Test getting clients for a workspace."""
        workspace_id = 12345
        mock_response = [
            {
                "id": 2001,
                "name": "Acme Corp",
                "wid": workspace_id,
                "archived": False,
                "notes": "Main client",
                "external_reference": "EXT-001",
                "at": "2024-01-01T10:00:00Z",
                "creator_id": 123
            },
            {
                "id": 2002,
                "name": "Tech Startup",
                "wid": workspace_id,
                "archived": True,
                "notes": None,
                "external_reference": None,
                "at": "2024-01-02T10:00:00Z",
                "creator_id": 123
            }
        ]

        respx.get(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/clients").respond(
            status_code=200,
            json=mock_response
        )

        result = await mock_toggl_client.get_clients(workspace_id)

        assert len(result) == 2
        assert isinstance(result[0], Client)
        assert result[0].id == 2001
        assert result[0].name == "Acme Corp"
        assert result[0].archived is False
        assert result[0].notes == "Main client"

    @respx.mock
    async def test_get_clients_with_filters(self, mock_toggl_client: TogglClient):
        """Test getting clients with status and name filters."""
        workspace_id = 12345
        mock_response = [
            {
                "id": 2001,
                "name": "Acme Corp",
                "wid": workspace_id,
                "archived": False,
                "notes": None,
                "external_reference": None
            }
        ]

        respx.get(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/clients").respond(
            status_code=200,
            json=mock_response
        )

        result = await mock_toggl_client.get_clients(workspace_id, status="active", name="Acme")

        assert len(result) == 1
        assert result[0].name == "Acme Corp"

    @respx.mock
    async def test_get_client(self, mock_toggl_client: TogglClient):
        """Test getting a specific client."""
        workspace_id = 12345
        client_id = 2001
        mock_response = {
            "id": client_id,
            "name": "Acme Corp",
            "wid": workspace_id,
            "archived": False,
            "notes": "Main client",
            "external_reference": "EXT-001",
            "at": "2024-01-01T10:00:00Z",
            "creator_id": 123
        }

        respx.get(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/clients/{client_id}").respond(
            status_code=200,
            json=mock_response
        )

        result = await mock_toggl_client.get_client(workspace_id, client_id)

        assert result is not None
        assert isinstance(result, Client)
        assert result.id == client_id
        assert result.name == "Acme Corp"
        assert result.notes == "Main client"

    @respx.mock
    async def test_create_client(self, mock_toggl_client: TogglClient):
        """Test creating a new client."""
        workspace_id = 12345
        mock_response = {
            "id": 2003,
            "name": "New Client Ltd",
            "wid": workspace_id,
            "archived": False,
            "notes": "New business partner",
            "external_reference": "EXT-003",
            "at": "2024-01-03T10:00:00Z",
            "creator_id": 123
        }

        respx.post(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/clients").respond(
            status_code=200,
            json=mock_response
        )

        result = await mock_toggl_client.create_client(
            workspace_id=workspace_id,
            name="New Client Ltd",
            notes="New business partner",
            external_reference="EXT-003"
        )

        assert result.id == 2003
        assert result.name == "New Client Ltd"
        assert result.notes == "New business partner"
        assert result.external_reference == "EXT-003"

    @respx.mock
    async def test_update_client(self, mock_toggl_client: TogglClient):
        """Test updating an existing client."""
        workspace_id = 12345
        client_id = 2001
        mock_response = {
            "id": client_id,
            "name": "Updated Client Name",
            "wid": workspace_id,
            "archived": False,
            "notes": "Updated notes",
            "external_reference": "EXT-UPDATED",
            "at": "2024-01-04T10:00:00Z",
            "creator_id": 123
        }

        respx.put(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/clients/{client_id}").respond(
            status_code=200,
            json=mock_response
        )

        result = await mock_toggl_client.update_client(
            workspace_id=workspace_id,
            client_id=client_id,
            name="Updated Client Name",
            notes="Updated notes",
            external_reference="EXT-UPDATED"
        )

        assert result.id == client_id
        assert result.name == "Updated Client Name"
        assert result.notes == "Updated notes"
        assert result.external_reference == "EXT-UPDATED"

    @respx.mock
    async def test_delete_client(self, mock_toggl_client: TogglClient):
        """Test deleting a client."""
        workspace_id = 12345
        client_id = 2001

        respx.delete(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/clients/{client_id}").respond(
            status_code=200
        )

        result = await mock_toggl_client.delete_client(workspace_id, client_id)
        assert result

    @respx.mock
    async def test_archive_client(self, mock_toggl_client: TogglClient):
        """Test archiving a client."""
        workspace_id = 12345
        client_id = 2001
        mock_response = [111, 222]  # Archived project IDs

        respx.post(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/clients/{client_id}/archive").respond(
            status_code=200,
            json=mock_response
        )

        result = await mock_toggl_client.archive_client(workspace_id, client_id)
        assert result == [111, 222]

    @respx.mock
    async def test_restore_client(self, mock_toggl_client: TogglClient):
        """Test restoring an archived client."""
        workspace_id = 12345
        client_id = 2001
        mock_response = {
            "id": client_id,
            "name": "Restored Client",
            "wid": workspace_id,
            "archived": False,
            "notes": "Restored",
            "external_reference": None,
            "at": "2024-01-05T10:00:00Z",
            "creator_id": 123
        }

        respx.post(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/clients/{client_id}/restore").respond(
            status_code=200,
            json=mock_response
        )

        result = await mock_toggl_client.restore_client(
            workspace_id=workspace_id,
            client_id=client_id,
            restore_all_projects=True
        )

        assert isinstance(result, Client)
        assert result.id == client_id
        assert result.name == "Restored Client"
        assert result.archived is False

    @respx.mock
    async def test_restore_client_with_project_ids(self, mock_toggl_client: TogglClient):
        """Test restoring a client with specific project IDs."""
        workspace_id = 12345
        client_id = 2001
        mock_response = {
            "id": client_id,
            "name": "Restored Client",
            "wid": workspace_id,
            "archived": False,
            "notes": None,
            "external_reference": None,
            "at": "2024-01-05T10:00:00Z",
            "creator_id": 123
        }

        respx.post(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/clients/{client_id}/restore").respond(
            status_code=200,
            json=mock_response
        )

        result = await mock_toggl_client.restore_client(
            workspace_id=workspace_id,
            client_id=client_id,
            project_ids=[111, 222]
        )

        assert isinstance(result, Client)
        assert result.id == client_id

    @respx.mock
    async def test_get_project(self, mock_toggl_client: TogglClient):
        """Test getting a specific project."""
        workspace_id = 12345
        project_id = 3001
        mock_response = {
            "id": project_id,
            "name": "Test Project",
            "workspace_id": workspace_id,
            "active": True,
            "color": "#3750b5",
            "billable": True,
            "is_private": False,
            "client_id": 2001
        }

        respx.get(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/projects/{project_id}").respond(
            status_code=200,
            json=mock_response
        )

        result = await mock_toggl_client.get_project(workspace_id, project_id)

        assert result is not None
        assert isinstance(result, Project)
        assert result.id == project_id
        assert result.name == "Test Project"
        assert result.billable is True

    @respx.mock
    async def test_create_project(self, mock_toggl_client: TogglClient):
        """Test creating a new project."""
        workspace_id = 12345
        mock_response = {
            "id": 3002,
            "name": "New Project",
            "workspace_id": workspace_id,
            "active": True,
            "color": "#06aaf5",
            "billable": False,
            "is_private": False,
            "client_id": None
        }

        respx.post(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/projects").respond(
            status_code=200,
            json=mock_response
        )

        result = await mock_toggl_client.create_project(
            workspace_id=workspace_id,
            name="New Project",
            color="#06aaf5",
            billable=False
        )

        assert result.id == 3002
        assert result.name == "New Project"
        assert result.color == "#06aaf5"
        assert result.billable is False

    @respx.mock
    async def test_update_project(self, mock_toggl_client: TogglClient):
        """Test updating an existing project."""
        workspace_id = 12345
        project_id = 3001
        mock_response = {
            "id": project_id,
            "name": "Updated Project",
            "workspace_id": workspace_id,
            "active": False,
            "color": "#c56bff",
            "billable": True,
            "is_private": True,
            "client_id": 2002
        }

        respx.put(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/projects/{project_id}").respond(
            status_code=200,
            json=mock_response
        )

        result = await mock_toggl_client.update_project(
            workspace_id=workspace_id,
            project_id=project_id,
            name="Updated Project",
            active=False,
            color="#c56bff",
            billable=True,
            is_private=True,
            client_id=2002
        )

        assert result.id == project_id
        assert result.name == "Updated Project"
        assert result.active is False
        assert result.color == "#c56bff"
        assert result.billable is True
        assert result.is_private is True

    @respx.mock
    async def test_delete_project(self, mock_toggl_client: TogglClient):
        """Test deleting a project."""
        workspace_id = 12345
        project_id = 3001

        respx.delete(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/projects/{project_id}").respond(
            status_code=200
        )

        result = await mock_toggl_client.delete_project(workspace_id, project_id)
        assert result

    # Workspace Users tests
    @respx.mock
    async def test_get_workspace_users(self, mock_toggl_client: TogglClient):
        """Test getting workspace users."""
        workspace_id = 12345
        mock_response = [
            {
                "id": 1001,
                "email": "user1@example.com",
                "fullname": "User One",
                "inactive": False,
                "is_active": True,
                "is_admin": True,
                "role": "admin"
            },
            {
                "id": 1002,
                "email": "user2@example.com",
                "fullname": "User Two",
                "inactive": False,
                "is_active": True,
                "is_admin": False,
                "role": "user"
            }
        ]

        respx.get(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/users").respond(
            status_code=200,
            json=mock_response
        )

        result = await mock_toggl_client.get_workspace_users(workspace_id)

        assert len(result) == 2
        assert result[0].id == 1001
        assert result[0].email == "user1@example.com"
        assert result[0].fullname == "User One"
        assert result[0].is_admin is True
        assert result[1].id == 1002
        assert result[1].role == "user"

    # Project Users tests
    @respx.mock
    async def test_get_project_users(self, mock_toggl_client: TogglClient):
        """Test getting project users."""
        workspace_id = 12345
        mock_response = [
            {
                "id": 5001,
                "user_id": 1001,
                "project_id": 3001,
                "workspace_id": workspace_id,
                "manager": True,
                "rate": 50.0,
                "labor_cost": 100.0,
                "at": "2024-01-15T10:00:00Z"
            }
        ]

        respx.get(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/project_users").respond(
            status_code=200,
            json=mock_response
        )

        result = await mock_toggl_client.get_project_users(workspace_id)

        assert len(result) == 1
        assert result[0].id == 5001
        assert result[0].user_id == 1001
        assert result[0].project_id == 3001
        assert result[0].manager is True
        assert result[0].rate == 50.0

    @respx.mock
    async def test_add_project_user(self, mock_toggl_client: TogglClient):
        """Test adding a user to a project."""
        workspace_id = 12345
        project_id = 3001
        user_id = 1001
        mock_response = {
            "id": 5001,
            "user_id": user_id,
            "project_id": project_id,
            "workspace_id": workspace_id,
            "manager": True,
            "rate": 75.0,
            "labor_cost": 150.0,
            "at": "2024-01-15T10:00:00Z"
        }

        respx.post(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/project_users").respond(
            status_code=200,
            json=mock_response
        )

        result = await mock_toggl_client.add_project_user(
            workspace_id=workspace_id,
            project_id=project_id,
            user_id=user_id,
            manager=True,
            rate=75.0,
            labor_cost=150.0
        )

        assert result.id == 5001
        assert result.user_id == user_id
        assert result.project_id == project_id
        assert result.manager is True
        assert result.rate == 75.0
        assert result.labor_cost == 150.0

    @respx.mock
    async def test_update_project_user(self, mock_toggl_client: TogglClient):
        """Test updating a project user."""
        workspace_id = 12345
        project_user_id = 5001
        mock_response = {
            "id": project_user_id,
            "user_id": 1001,
            "project_id": 3001,
            "workspace_id": workspace_id,
            "manager": False,
            "rate": 100.0,
            "labor_cost": 200.0,
            "at": "2024-01-15T11:00:00Z"
        }

        respx.put(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/project_users/{project_user_id}").respond(
            status_code=200,
            json=mock_response
        )

        result = await mock_toggl_client.update_project_user(
            workspace_id=workspace_id,
            project_user_id=project_user_id,
            manager=False,
            rate=100.0,
            labor_cost=200.0
        )

        assert result.id == project_user_id
        assert result.manager is False
        assert result.rate == 100.0
        assert result.labor_cost == 200.0

    @respx.mock
    async def test_delete_project_user(self, mock_toggl_client: TogglClient):
        """Test deleting a project user."""
        workspace_id = 12345
        project_user_id = 5001

        respx.delete(f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/project_users/{project_user_id}").respond(
            status_code=200
        )

        result = await mock_toggl_client.delete_project_user(workspace_id, project_user_id)
        assert result