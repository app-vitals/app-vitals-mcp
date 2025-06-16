"""Integration tests for TogglServer."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from app_vitals_mcp.servers.toggl.config import TogglConfig
from app_vitals_mcp.servers.toggl.server import TogglServer
from app_vitals_mcp.servers.toggl.models import TimeEntry, Workspace, Project


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
        server.client.close = AsyncMock()
        
        yield server
        await server.client.close()

    async def test_get_current_time_entry_none(self, mock_server: TogglServer):
        """Test getting current time entry when none is running."""
        mock_server.timer_service.get_current_timer.return_value = None
        
        # Get the tool function
        tools = mock_server.mcp._tool_manager._tools
        get_current_time_entry = tools["get_current_time_entry"]
        
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
        get_current_time_entry = tools["get_current_time_entry"]
        
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
        start_timer = tools["start_timer"]
        
        result = await start_timer.fn(description="New task", project_id=111)
        
        assert result["id"] == 456
        assert result["description"] == "New task"
        mock_server.timer_service.start_timer.assert_called_once_with(
            "New task", 111, None
        )

    async def test_stop_timer_no_running(self, mock_server: TogglServer):
        """Test stopping timer when none is running."""
        mock_server.timer_service.stop_current_timer.return_value = None
        
        tools = mock_server.mcp._tool_manager._tools
        stop_timer = tools["stop_timer"]
        
        result = await stop_timer.fn()
        assert result == {"status": "No time entry currently running"}

    async def test_stop_timer_success(self, mock_server: TogglServer):
        """Test successfully stopping a timer."""
        running_entry = TimeEntry(
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
        stop_timer = tools["stop_timer"]
        
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
        get_time_entries = tools["get_time_entries"]
        
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
        get_workspaces = tools["get_workspaces"]
        
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
        get_projects = tools["get_projects"]
        
        result = await get_projects.fn(workspace_id=12345)
        
        assert len(result) == 2
        assert result[0]["name"] == "Project A"
        assert result[1]["name"] == "Project B"

    async def test_get_time_summary(self, mock_server: TogglServer):
        """Test getting time summary."""
        mock_entries = [
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
        get_time_summary = tools["get_time_summary"]
        
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
        create_time_entry = tools["create_time_entry"]
        
        result = await create_time_entry.fn(
            description="Completed task",
            start_time="2024-01-01T10:00:00Z",
            duration_minutes=90,
            project_id=222,
            tags=["development"],
            billable=True
        )
        
        assert result["id"] == 123
        assert result["description"] == "Completed task"
        assert result["duration"] == 5400
        assert result["billable"] == True
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
        get_time_entry = tools["get_time_entry"]
        
        result = await get_time_entry.fn(time_entry_id=456)
        
        assert result["id"] == 456
        assert result["description"] == "Retrieved task"

    async def test_get_time_entry_not_found(self, mock_server: TogglServer):
        """Test getting a time entry that doesn't exist."""
        mock_server.entry_service.get_entry.return_value = None
        
        tools = mock_server.mcp._tool_manager._tools
        get_time_entry = tools["get_time_entry"]
        
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
        update_time_entry = tools["update_time_entry"]
        
        result = await update_time_entry.fn(
            time_entry_id=789,
            description="Updated task",
            duration_minutes=120,
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
        delete_time_entry = tools["delete_time_entry"]
        
        result = await delete_time_entry.fn(time_entry_id=555)
        
        assert result["success"] == True
        assert "deleted" in result["message"]

    async def test_delete_time_entry_failure(self, mock_server: TogglServer):
        """Test failed time entry deletion."""
        mock_server.entry_service.delete_entry.return_value = False
        
        tools = mock_server.mcp._tool_manager._tools
        delete_time_entry = tools["delete_time_entry"]
        
        result = await delete_time_entry.fn(time_entry_id=999)
        
        assert result["success"] == False
        assert "Failed to delete" in result["message"]


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
        get_workspaces = tools["get_workspaces"]
        
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
        get_current_time_entry = tools["get_current_time_entry"]
        
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
        get_time_entries = tools["get_time_entries"]
        
        result = await get_time_entries.fn(days_back=30)
        
        assert isinstance(result, list)
        # Note: May be empty if user has no time entries