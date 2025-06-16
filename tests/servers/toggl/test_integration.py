"""End-to-end integration tests for Toggl MCP server."""

import pytest
import pytest_asyncio
import asyncio
import os
from typing import Optional

from app_vitals_mcp.servers.toggl.config import TogglConfig
from app_vitals_mcp.servers.toggl.server import TogglServer
from app_vitals_mcp.servers.toggl.client import TogglClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestTogglIntegration:
    """Integration tests that require real Toggl API access."""

    @pytest_asyncio.fixture
    async def integration_client(self, real_api_token: Optional[str]):
        """Create a real Toggl client for integration testing."""
        client = TogglClient(real_api_token)
        yield client
        await client.close()

    @pytest_asyncio.fixture
    async def integration_server(self, real_config: Optional[TogglConfig]):
        """Create a real Toggl server for integration testing."""
        server = TogglServer(real_config)
        yield server
        await server.client.close()

    async def test_api_authentication(self, integration_client: TogglClient):
        """Test that API authentication works."""
        user_info = await integration_client.get_current_user()
        
        assert "id" in user_info
        assert "email" in user_info
        assert isinstance(user_info["id"], int)

    async def test_get_workspaces(self, integration_client: TogglClient):
        """Test getting workspaces from real API."""
        workspaces = await integration_client.get_workspaces()
        
        assert isinstance(workspaces, list)
        if workspaces:  # User should have at least one workspace
            workspace = workspaces[0]
            assert hasattr(workspace, "id")
            assert hasattr(workspace, "name")
            assert hasattr(workspace, "organization_id")

    async def test_get_projects(self, integration_client: TogglClient):
        """Test getting projects from real API."""
        workspaces = await integration_client.get_workspaces()
        workspace_id = workspaces[0].id
        projects = await integration_client.get_projects(workspace_id)
        
        assert isinstance(projects, list)
        # Note: Projects list may be empty

    async def test_get_time_entries(self, integration_client: TogglClient):
        """Test getting time entries from real API."""
        from datetime import datetime, timedelta
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        entries = await integration_client.get_time_entries(
            start_date.isoformat() + "Z",
            end_date.isoformat() + "Z"
        )
        
        assert isinstance(entries, list)
        # Note: Time entries list may be empty

    async def test_get_current_time_entry(self, integration_client: TogglClient):
        """Test getting current time entry from real API."""
        current_entry = await integration_client.get_current_time_entry()
        
        # Should be None if no timer is running, or a TimeEntry if one is running
        if current_entry is not None:
            assert hasattr(current_entry, "id")
            assert hasattr(current_entry, "workspace_id")
            assert current_entry.duration < 0  # Running entries have negative duration

    async def test_server_tools_basic(self, integration_server: TogglServer):
        """Test basic server tools functionality."""
        # Get tools
        tools = integration_server.mcp._tool_manager._tools
        
        # Test get_workspaces
        workspaces_result = await tools["get_workspaces"].fn()
        assert isinstance(workspaces_result, list)
        
        # Test get_current_time_entry
        current_result = await tools["get_current_time_entry"].fn()
        assert isinstance(current_result, dict)
        
        # Test get_time_entries
        entries_result = await tools["get_time_entries"].fn(days_back=7)
        assert isinstance(entries_result, list)
        
        # Test get_time_summary
        summary_result = await tools["get_time_summary"].fn(days_back=7)
        assert isinstance(summary_result, dict)
        assert "total_hours" in summary_result
        assert "total_entries" in summary_result

    @pytest.mark.slow
    async def test_start_stop_timer_workflow(self, integration_server: TogglServer):
        """Test complete start/stop timer workflow."""
        tools = integration_server.mcp._tool_manager._tools
        
        # Get available projects and find the test project
        projects = await tools["get_projects"].fn()
        test_project = next((p for p in projects if p["name"] == "Integration Tests"), None)
        if not test_project:
            pytest.fail("Integration Tests project not found - please create a project named 'Integration Tests' in your Toggl workspace")
        
        project_id = test_project["id"]
        
        # Check current state
        current_before = await tools["get_current_time_entry"].fn()
        
        # If there's already a timer running, stop it first
        if "status" not in current_before:
            await tools["stop_timer"].fn()
            await asyncio.sleep(2)  # Wait for API consistency
        
        # Start a new timer (using the Integration Tests project)
        start_result = await tools["start_timer"].fn(
            description="Integration test timer - safe to delete",
            project_id=project_id
        )
        assert "id" in start_result
        assert start_result["description"] == "Integration test timer - safe to delete"
        
        # Wait a moment for API consistency
        await asyncio.sleep(3)
        
        # Check that timer is running
        current_running = await tools["get_current_time_entry"].fn()
        assert "status" not in current_running  # Should have a running entry
        assert current_running["id"] == start_result["id"]
        
        # Stop the timer
        stop_result = await tools["stop_timer"].fn()
        assert stop_result["id"] == start_result["id"]
        assert stop_result["duration"] > 0  # Should have positive duration when stopped
        
        # Wait a moment for API consistency
        await asyncio.sleep(2)
        
        # Check that no timer is running
        current_after = await tools["get_current_time_entry"].fn()
        assert current_after.get("status") == "No time entry currently running"

    async def test_error_handling(self, real_api_token: Optional[str]):
        """Test error handling with invalid requests."""
        client = TogglClient(real_api_token)
        
        try:
            # Test with invalid workspace ID
            with pytest.raises(Exception):  # Should raise HTTP error
                await client.get_projects(999999)
        finally:
            await client.close()

    async def test_rate_limiting_compliance(self, integration_client: TogglClient):
        """Test that we handle rate limiting appropriately."""
        # Make several requests in quick succession
        tasks = []
        for _ in range(3):
            tasks.append(integration_client.get_current_user())
        
        # Should not raise rate limiting errors with reasonable spacing
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that we got responses (may be exceptions but shouldn't be rate limit errors)
        assert len(results) == 3
        
        # At least some should succeed
        successes = [r for r in results if not isinstance(r, Exception)]
        assert len(successes) > 0


def test_environment_setup():
    """Test that environment variables are properly configured."""
    api_token = os.getenv("TOGGL_API_TOKEN")
    
    if api_token:
        assert len(api_token) > 10  # Basic sanity check
        assert api_token.strip() == api_token  # No whitespace
    
    workspace_id = os.getenv("TOGGL_WORKSPACE_ID")
    if workspace_id:
        assert workspace_id.isdigit()  # Should be numeric
