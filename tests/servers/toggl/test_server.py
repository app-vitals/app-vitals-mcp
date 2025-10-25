"""Integration tests for TogglServer."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock

from app_vitals_mcp.servers.toggl.config import TogglConfig
from app_vitals_mcp.servers.toggl.server import TogglServer
from app_vitals_mcp.servers.toggl.models import TimeEntry, Workspace, Project, Task, Client


@pytest.mark.unit
@pytest.mark.asyncio
class TestTogglServerUnit:
    """Unit tests for TogglServer with mocked dependencies."""

    @pytest_asyncio.fixture
    async def mock_server(self, test_config: TogglConfig):
        """Create TogglServer with mocked client."""
        server = TogglServer(test_config)
        
        # Mock the service methods
        server.timer_service.get_current_timer = AsyncMock()
        server.timer_service.start_timer = AsyncMock()
        server.timer_service.stop_current_timer = AsyncMock()
        server.entry_service.create_entry = AsyncMock()
        server.entry_service.get_entry = AsyncMock()
        server.entry_service.update_entry = AsyncMock()
        server.entry_service.delete_entry = AsyncMock()
        server.analytics_service.get_time_entries = AsyncMock()
        server.analytics_service.get_time_summary = AsyncMock()
        server.workspace_service.get_workspaces = AsyncMock()
        server.workspace_service.get_projects = AsyncMock()
        server.task_service.get_tasks = AsyncMock()
        server.task_service.get_task = AsyncMock()
        server.task_service.create_task = AsyncMock()
        server.task_service.update_task = AsyncMock()
        server.task_service.delete_task = AsyncMock()
        server.client_service.get_clients = AsyncMock()
        server.client_service.get_client = AsyncMock()
        server.client_service.create_client = AsyncMock()
        server.client_service.update_client = AsyncMock()
        server.client_service.delete_client = AsyncMock()
        server.client_service.archive_client = AsyncMock()
        server.client_service.restore_client = AsyncMock()
        server.client.close = AsyncMock()
        
        yield server
        await server.client.close()

    async def test_get_current_time_entry_none(self, mock_server: TogglServer):
        """Test getting current time entry when none is running."""
        mock_server.timer_service.get_current_timer.return_value = None
        
        # Get the tool function
        tools = mock_server.mcp._tool_manager._tools
        get_current_time_entry = tools["toggl_get_current_time_entry"]
        
        result = await get_current_time_entry.fn()
        assert result == {"status": "No time entry currently running"}

    async def test_get_current_time_entry_running(self, mock_server: TogglServer):
        """Test getting current time entry when one is running."""
        mock_entry = TimeEntry(
            id=123,
            description="Test task",
            start="2024-01-01T10:00:00Z",
            duration=-1,
            workspace_id=12345
        )
        mock_server.timer_service.get_current_timer.return_value = mock_entry
        
        tools = mock_server.mcp._tool_manager._tools
        get_current_time_entry = tools["toggl_get_current_time_entry"]
        
        result = await get_current_time_entry.fn()
        assert result["id"] == 123
        assert result["description"] == "Test task"

    async def test_start_timer(self, mock_server: TogglServer):
        """Test starting a timer."""
        mock_entry = TimeEntry(
            id=456,
            description="New task",
            start="2024-01-01T11:00:00Z",
            duration=-1,
            workspace_id=12345
        )
        
        # Mock workspace retrieval
        mock_server.timer_service.start_timer.return_value = mock_entry
        
        tools = mock_server.mcp._tool_manager._tools
        start_timer = tools["toggl_start_timer"]
        
        result = await start_timer.fn(description="New task", project_id=111, task_id=1001)
        
        assert result["id"] == 456
        assert result["description"] == "New task"
        mock_server.timer_service.start_timer.assert_called_once_with(
            "New task", 111, 1001, None
        )

    async def test_stop_timer_no_running(self, mock_server: TogglServer):
        """Test stopping timer when none is running."""
        mock_server.timer_service.stop_current_timer.return_value = None
        
        tools = mock_server.mcp._tool_manager._tools
        stop_timer = tools["toggl_stop_timer"]
        
        result = await stop_timer.fn()
        assert result == {"status": "No time entry currently running"}

    async def test_stop_timer_success(self, mock_server: TogglServer):
        """Test successfully stopping a timer."""
        TimeEntry(
            id=789,
            description="Running task",
            start="2024-01-01T12:00:00Z",
            duration=-1,
            workspace_id=12345
        )
        stopped_entry = TimeEntry(
            id=789,
            description="Running task",
            start="2024-01-01T12:00:00Z",
            stop="2024-01-01T13:00:00Z",
            duration=3600,
            workspace_id=12345
        )
        
        mock_server.timer_service.stop_current_timer.return_value = stopped_entry
        
        tools = mock_server.mcp._tool_manager._tools
        stop_timer = tools["toggl_stop_timer"]
        
        result = await stop_timer.fn()
        
        assert result["id"] == 789
        assert result["duration"] == 3600

    async def test_get_time_entries(self, mock_server: TogglServer):
        """Test getting time entries."""
        mock_entries = [
            TimeEntry(
                id=1,
                description="Task 1",
                start="2024-01-01T10:00:00Z",
                stop="2024-01-01T11:00:00Z",
                duration=3600,
                workspace_id=12345
            ),
            TimeEntry(
                id=2,
                description="Task 2",
                start="2024-01-01T14:00:00Z",
                stop="2024-01-01T15:30:00Z",
                duration=5400,
                workspace_id=12345
            )
        ]
        mock_server.analytics_service.get_time_entries.return_value = mock_entries
        
        tools = mock_server.mcp._tool_manager._tools
        get_time_entries = tools["toggl_get_time_entries"]
        
        result = await get_time_entries.fn(days_back=3)
        
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2

    async def test_get_workspaces(self, mock_server: TogglServer):
        """Test getting workspaces."""
        mock_workspaces = [
            Workspace(id=12345, name="Workspace 1", organization_id=1),
            Workspace(id=67890, name="Workspace 2", organization_id=1)
        ]
        mock_server.workspace_service.get_workspaces.return_value = mock_workspaces
        
        tools = mock_server.mcp._tool_manager._tools
        get_workspaces = tools["toggl_get_workspaces"]
        
        result = await get_workspaces.fn()
        
        assert len(result) == 2
        assert result[0]["name"] == "Workspace 1"
        assert result[1]["name"] == "Workspace 2"

    async def test_get_projects(self, mock_server: TogglServer):
        """Test getting projects."""
        mock_projects = [
            Project(id=111, name="Project A", workspace_id=12345),
            Project(id=222, name="Project B", workspace_id=12345)
        ]
        mock_server.workspace_service.get_projects.return_value = mock_projects
        
        tools = mock_server.mcp._tool_manager._tools
        get_projects = tools["toggl_get_projects"]
        
        result = await get_projects.fn(workspace_id=12345)
        
        assert len(result) == 2
        assert result[0]["name"] == "Project A"
        assert result[1]["name"] == "Project B"

    async def test_get_time_summary(self, mock_server: TogglServer):
        """Test getting time summary."""
        [
            TimeEntry(
                id=1,
                description="Task 1",
                start="2024-01-01T10:00:00Z",
                stop="2024-01-01T12:00:00Z",
                duration=7200,  # 2 hours
                project_id=111,
                workspace_id=12345
            ),
            TimeEntry(
                id=2,
                description="Task 2",
                start="2024-01-01T14:00:00Z",
                stop="2024-01-01T15:30:00Z",
                duration=5400,  # 1.5 hours
                project_id=222,
                workspace_id=12345
            ),
            TimeEntry(
                id=3,
                description="Task 3",
                start="2024-01-01T16:00:00Z",
                stop="2024-01-01T17:00:00Z",
                duration=3600,  # 1 hour
                project_id=111,
                workspace_id=12345
            )
        ]
        mock_server.analytics_service.get_time_summary.return_value = {
            "total_hours": 4.5,
            "total_entries": 3,
            "project_breakdown": {"111": 3.0, "222": 1.5},
            "period_days": 7
        }
        
        tools = mock_server.mcp._tool_manager._tools
        get_time_summary = tools["toggl_get_time_summary"]
        
        result = await get_time_summary.fn(days_back=7)
        
        assert result["total_hours"] == 4.5  # 2 + 1.5 + 1
        assert result["total_entries"] == 3
        assert result["project_breakdown"]["111"] == 3.0  # 2 + 1
        assert result["project_breakdown"]["222"] == 1.5
        assert result["period_days"] == 7

    async def test_create_time_entry(self, mock_server: TogglServer):
        """Test creating a completed time entry."""
        mock_entry = TimeEntry(
            id=123,
            description="Completed task",
            start="2024-01-01T10:00:00Z",
            stop="2024-01-01T11:30:00Z",
            duration=5400,  # 90 minutes
            workspace_id=12345,
            tags=["development"],
            billable=True
        )
        
        mock_server.entry_service.create_entry.return_value = mock_entry
        
        tools = mock_server.mcp._tool_manager._tools
        create_time_entry = tools["toggl_create_time_entry"]
        
        result = await create_time_entry.fn(
            description="Completed task",
            start_time="2024-01-01T10:00:00Z",
            duration_minutes=90,
            project_id=222,
            task_id=1002,
            tags=["development"],
            billable=True
        )
        
        assert result["id"] == 123
        assert result["description"] == "Completed task"
        assert result["duration"] == 5400
        assert result["billable"]
        assert result["tags"] == ["development"]

    async def test_get_time_entry_found(self, mock_server: TogglServer):
        """Test getting a specific time entry that exists."""
        mock_entry = TimeEntry(
            id=456,
            description="Retrieved task",
            start="2024-01-01T14:00:00Z",
            stop="2024-01-01T15:00:00Z",
            duration=3600,
            workspace_id=12345
        )
        
        mock_server.entry_service.get_entry.return_value = mock_entry
        
        tools = mock_server.mcp._tool_manager._tools
        get_time_entry = tools["toggl_get_time_entry"]
        
        result = await get_time_entry.fn(time_entry_id=456)
        
        assert result["id"] == 456
        assert result["description"] == "Retrieved task"

    async def test_get_time_entry_not_found(self, mock_server: TogglServer):
        """Test getting a time entry that doesn't exist."""
        mock_server.entry_service.get_entry.return_value = None
        
        tools = mock_server.mcp._tool_manager._tools
        get_time_entry = tools["toggl_get_time_entry"]
        
        result = await get_time_entry.fn(time_entry_id=999)
        
        assert "error" in result
        assert result["error"] == "Time entry not found"

    async def test_update_time_entry(self, mock_server: TogglServer):
        """Test updating an existing time entry."""
        updated_entry = TimeEntry(
            id=789,
            description="Updated task",
            start="2024-01-01T10:00:00Z",
            stop="2024-01-01T12:00:00Z",
            duration=7200,  # 2 hours
            workspace_id=12345,
            tags=["updated"],
            billable=False
        )
        
        mock_server.entry_service.update_entry.return_value = updated_entry
        
        tools = mock_server.mcp._tool_manager._tools
        update_time_entry = tools["toggl_update_time_entry"]
        
        result = await update_time_entry.fn(
            time_entry_id=789,
            description="Updated task",
            duration_minutes=120,
            task_id=1003,
            tags=["updated"],
            billable=False
        )
        
        assert result["id"] == 789
        assert result["description"] == "Updated task"
        assert result["duration"] == 7200

    async def test_delete_time_entry_success(self, mock_server: TogglServer):
        """Test successfully deleting a time entry."""
        mock_server.entry_service.delete_entry.return_value = True
        
        tools = mock_server.mcp._tool_manager._tools
        delete_time_entry = tools["toggl_delete_time_entry"]
        
        result = await delete_time_entry.fn(time_entry_id=555)
        
        assert result["success"]
        assert "deleted" in result["message"]

    async def test_delete_time_entry_failure(self, mock_server: TogglServer):
        """Test failed time entry deletion."""
        mock_server.entry_service.delete_entry.return_value = False
        
        tools = mock_server.mcp._tool_manager._tools
        delete_time_entry = tools["toggl_delete_time_entry"]
        
        result = await delete_time_entry.fn(time_entry_id=999)
        
        assert not result["success"]
        assert "Failed to delete" in result["message"]

    async def test_get_tasks(self, mock_server: TogglServer):
        """Test getting tasks through MCP tool."""
        mock_tasks = [
            Task(
                id=1001,
                name="Design mockups",
                project_id=111,
                workspace_id=12345,
                active=True,
                estimated_seconds=7200,
                tracked_seconds=3600
            ),
            Task(
                id=1002,
                name="Code review",
                project_id=111,
                workspace_id=12345,
                active=True,
                estimated_seconds=None,
                tracked_seconds=1800
            )
        ]
        
        mock_server.task_service.get_tasks.return_value = mock_tasks
        
        tools = mock_server.mcp._tool_manager._tools
        get_tasks = tools["toggl_get_tasks"]
        
        result = await get_tasks.fn(project_id=111, active=True)
        
        assert len(result) == 2
        assert result[0]["id"] == 1001
        assert result[0]["name"] == "Design mockups"
        assert result[1]["id"] == 1002
        assert result[1]["name"] == "Code review"

    async def test_get_task(self, mock_server: TogglServer):
        """Test getting a specific task through MCP tool."""
        mock_task = Task(
            id=1001,
            name="Design mockups",
            project_id=111,
            workspace_id=12345,
            active=True,
            estimated_seconds=7200,
            tracked_seconds=3600
        )
        
        mock_server.task_service.get_task.return_value = mock_task
        
        tools = mock_server.mcp._tool_manager._tools
        get_task = tools["toggl_get_task"]
        
        result = await get_task.fn(project_id=111, task_id=1001)
        
        assert result["id"] == 1001
        assert result["name"] == "Design mockups"
        assert result["estimated_seconds"] == 7200

    async def test_get_task_not_found(self, mock_server: TogglServer):
        """Test getting a task that doesn't exist."""
        mock_server.task_service.get_task.return_value = None
        
        tools = mock_server.mcp._tool_manager._tools
        get_task = tools["toggl_get_task"]
        
        result = await get_task.fn(project_id=111, task_id=999)
        
        assert "error" in result
        assert result["error"] == "Task not found"

    async def test_create_task(self, mock_server: TogglServer):
        """Test creating a new task through MCP tool."""
        mock_task = Task(
            id=1003,
            name="New feature implementation",
            project_id=111,
            workspace_id=12345,
            active=True,
            estimated_seconds=14400,
            tracked_seconds=0
        )
        
        mock_server.task_service.create_task.return_value = mock_task
        
        tools = mock_server.mcp._tool_manager._tools
        create_task = tools["toggl_create_task"]
        
        result = await create_task.fn(
            project_id=111,
            name="New feature implementation",
            estimated_hours=4.0,
            active=True
        )
        
        assert result["id"] == 1003
        assert result["name"] == "New feature implementation"
        assert result["estimated_seconds"] == 14400
        mock_server.task_service.create_task.assert_called_once_with(
            111, "New feature implementation", 14400, True
        )

    async def test_update_task(self, mock_server: TogglServer):
        """Test updating an existing task through MCP tool."""
        updated_task = Task(
            id=1001,
            name="Updated task name",
            project_id=111,
            workspace_id=12345,
            active=False,
            estimated_seconds=10800,
            tracked_seconds=3600
        )
        
        mock_server.task_service.update_task.return_value = updated_task
        
        tools = mock_server.mcp._tool_manager._tools
        update_task = tools["toggl_update_task"]
        
        result = await update_task.fn(
            project_id=111,
            task_id=1001,
            name="Updated task name",
            estimated_hours=3.0,
            active=False
        )
        
        assert result["id"] == 1001
        assert result["name"] == "Updated task name"
        assert not result["active"]
        assert result["estimated_seconds"] == 10800

    async def test_delete_task_success(self, mock_server: TogglServer):
        """Test successfully deleting a task through MCP tool."""
        mock_server.task_service.delete_task.return_value = True
        
        tools = mock_server.mcp._tool_manager._tools
        delete_task = tools["toggl_delete_task"]
        
        result = await delete_task.fn(project_id=111, task_id=1001)
        
        assert result["success"]
        assert "deleted successfully" in result["message"]

    async def test_delete_task_failure(self, mock_server: TogglServer):
        """Test failed task deletion through MCP tool."""
        mock_server.task_service.delete_task.return_value = False
        
        tools = mock_server.mcp._tool_manager._tools
        delete_task = tools["toggl_delete_task"]
        
        result = await delete_task.fn(project_id=111, task_id=999)
        
        assert not result["success"]
        assert "Failed to delete" in result["message"]

    async def test_get_clients(self, mock_server: TogglServer):
        """Test getting clients through MCP tool."""
        mock_clients = [
            Client(
                id=2001,
                name="Acme Corp",
                wid=12345,
                archived=False,
                notes="Main client"
            ),
            Client(
                id=2002,
                name="Tech Startup",
                wid=12345,
                archived=False,
                notes=None
            )
        ]

        mock_server.client_service.get_clients.return_value = mock_clients

        tools = mock_server.mcp._tool_manager._tools
        get_clients = tools["toggl_get_clients"]

        result = await get_clients.fn(status="active")

        assert len(result) == 2
        assert result[0]["id"] == 2001
        assert result[0]["name"] == "Acme Corp"
        assert result[1]["id"] == 2002
        assert result[1]["name"] == "Tech Startup"

    async def test_get_client(self, mock_server: TogglServer):
        """Test getting a specific client through MCP tool."""
        mock_client = Client(
            id=2001,
            name="Acme Corp",
            wid=12345,
            archived=False,
            notes="Main client",
            external_reference="EXT-001"
        )

        mock_server.client_service.get_client.return_value = mock_client

        tools = mock_server.mcp._tool_manager._tools
        get_client = tools["toggl_get_client"]

        result = await get_client.fn(client_id=2001)

        assert result["id"] == 2001
        assert result["name"] == "Acme Corp"
        assert result["notes"] == "Main client"

    async def test_get_client_not_found(self, mock_server: TogglServer):
        """Test getting a client that doesn't exist."""
        mock_server.client_service.get_client.return_value = None

        tools = mock_server.mcp._tool_manager._tools
        get_client = tools["toggl_get_client"]

        result = await get_client.fn(client_id=999)

        assert "error" in result
        assert result["error"] == "Client not found"

    async def test_create_client(self, mock_server: TogglServer):
        """Test creating a new client through MCP tool."""
        mock_client = Client(
            id=2003,
            name="New Client Ltd",
            wid=12345,
            archived=False,
            notes="New business partner",
            external_reference="EXT-003"
        )

        mock_server.client_service.create_client.return_value = mock_client

        tools = mock_server.mcp._tool_manager._tools
        create_client = tools["toggl_create_client"]

        result = await create_client.fn(
            name="New Client Ltd",
            notes="New business partner",
            external_reference="EXT-003"
        )

        assert result["id"] == 2003
        assert result["name"] == "New Client Ltd"
        assert result["notes"] == "New business partner"
        mock_server.client_service.create_client.assert_called_once_with(
            "New Client Ltd", "New business partner", "EXT-003"
        )

    async def test_update_client(self, mock_server: TogglServer):
        """Test updating an existing client through MCP tool."""
        updated_client = Client(
            id=2001,
            name="Updated Client Name",
            wid=12345,
            archived=False,
            notes="Updated notes",
            external_reference="EXT-UPDATED"
        )

        mock_server.client_service.update_client.return_value = updated_client

        tools = mock_server.mcp._tool_manager._tools
        update_client = tools["toggl_update_client"]

        result = await update_client.fn(
            client_id=2001,
            name="Updated Client Name",
            notes="Updated notes",
            external_reference="EXT-UPDATED"
        )

        assert result["id"] == 2001
        assert result["name"] == "Updated Client Name"
        assert result["notes"] == "Updated notes"
        assert result["external_reference"] == "EXT-UPDATED"

    async def test_delete_client_success(self, mock_server: TogglServer):
        """Test successfully deleting a client through MCP tool."""
        mock_server.client_service.delete_client.return_value = True

        tools = mock_server.mcp._tool_manager._tools
        delete_client = tools["toggl_delete_client"]

        result = await delete_client.fn(client_id=2001)

        assert result["success"]
        assert "deleted successfully" in result["message"]

    async def test_delete_client_failure(self, mock_server: TogglServer):
        """Test failed client deletion through MCP tool."""
        mock_server.client_service.delete_client.return_value = False

        tools = mock_server.mcp._tool_manager._tools
        delete_client = tools["toggl_delete_client"]

        result = await delete_client.fn(client_id=999)

        assert not result["success"]
        assert "Failed to delete" in result["message"]

    async def test_archive_client(self, mock_server: TogglServer):
        """Test archiving a client through MCP tool."""
        mock_server.client_service.archive_client.return_value = [111, 222]

        tools = mock_server.mcp._tool_manager._tools
        archive_client = tools["toggl_archive_client"]

        result = await archive_client.fn(client_id=2001)

        assert result["success"]
        assert "archived successfully" in result["message"]
        assert result["archived_project_ids"] == [111, 222]

    async def test_restore_client(self, mock_server: TogglServer):
        """Test restoring an archived client through MCP tool."""
        restored_client = Client(
            id=2001,
            name="Restored Client",
            wid=12345,
            archived=False,
            notes="Restored"
        )

        mock_server.client_service.restore_client.return_value = restored_client

        tools = mock_server.mcp._tool_manager._tools
        restore_client = tools["toggl_restore_client"]

        result = await restore_client.fn(
            client_id=2001,
            restore_all_projects=True
        )

        assert result["id"] == 2001
        assert result["name"] == "Restored Client"
        assert result["archived"] is False


@pytest.mark.integration
@pytest.mark.asyncio
class TestTogglServerIntegration:
    """Integration tests that require real API token."""

    @pytest_asyncio.fixture
    async def real_server(self, real_config):
        """Create TogglServer with real API token."""
        if not real_config:
            pytest.skip("TOGGL_API_TOKEN not set in environment")
        
        server = TogglServer(real_config)
        yield server
        await server.client.close()

    async def test_get_workspaces_real(self, real_server):
        """Test getting real workspaces."""
        if not real_server:
            pytest.skip("Real API token not available")
        
        tools = real_server.mcp._tool_manager._tools
        get_workspaces = tools["toggl_get_workspaces"]
        
        result = await get_workspaces.fn()
        
        assert isinstance(result, list)
        if result:  # If user has workspaces
            assert "id" in result[0]
            assert "name" in result[0]

    async def test_get_current_time_entry_real(self, real_server):
        """Test getting real current time entry."""
        if not real_server:
            pytest.skip("Real API token not available")
        
        tools = real_server.mcp._tool_manager._tools
        get_current_time_entry = tools["toggl_get_current_time_entry"]
        
        result = await get_current_time_entry.fn()
        
        # Should either return a time entry or "no time entry running"
        assert isinstance(result, dict)
        if "status" not in result:  # If there's a running entry
            assert "id" in result
            assert "workspace_id" in result

    async def test_get_time_entries_real(self, real_server):
        """Test getting real time entries."""
        if not real_server:
            pytest.skip("Real API token not available")
        
        tools = real_server.mcp._tool_manager._tools
        get_time_entries = tools["toggl_get_time_entries"]
        
        result = await get_time_entries.fn(days_back=30)
        
        assert isinstance(result, list)
        # Note: May be empty if user has no time entries