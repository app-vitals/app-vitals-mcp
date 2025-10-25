"""End-to-end integration tests for Toggl MCP server."""

import pytest
import pytest_asyncio
import asyncio
import os
from typing import Optional
from datetime import datetime

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
        workspaces_result = await tools["toggl_get_workspaces"].fn()
        assert isinstance(workspaces_result, list)
        
        # Test get_current_time_entry
        current_result = await tools["toggl_get_current_time_entry"].fn()
        assert isinstance(current_result, dict)
        
        # Test get_time_entries
        entries_result = await tools["toggl_get_time_entries"].fn(days_back=7)
        assert isinstance(entries_result, list)
        
        # Test get_time_summary
        summary_result = await tools["toggl_get_time_summary"].fn(days_back=7)
        assert isinstance(summary_result, dict)
        assert "total_hours" in summary_result
        assert "total_entries" in summary_result

    @pytest.mark.slow
    async def test_start_stop_timer_workflow(self, integration_server: TogglServer):
        """Test complete start/stop timer workflow."""
        tools = integration_server.mcp._tool_manager._tools
        
        # Get available projects and find the test project
        projects = await tools["toggl_get_projects"].fn()
        test_project = next((p for p in projects if p["name"] == "Integration Tests"), None)
        if not test_project:
            pytest.fail("Integration Tests project not found - please create a project named 'Integration Tests' in your Toggl workspace")
        
        project_id = test_project["id"]
        
        # Check current state
        current_before = await tools["toggl_get_current_time_entry"].fn()
        
        # If there's already a timer running, stop it first
        if "status" not in current_before:
            await tools["toggl_stop_timer"].fn()
            await asyncio.sleep(2)  # Wait for API consistency
        
        # Get tasks for the project to find a task_id
        tasks = await tools["toggl_get_tasks"].fn(project_id=project_id)
        if not tasks:
            # Create a test task if none exist
            task_result = await tools["toggl_create_task"].fn(
                project_id=project_id,
                name="Integration test task - safe to delete",
                estimated_hours=1.0
            )
            task_id = task_result["id"]
        else:
            task_id = tasks[0]["id"]
        
        # Start a new timer (using the Integration Tests project and task)
        start_result = await tools["toggl_start_timer"].fn(
            description="Integration test timer - safe to delete",
            project_id=project_id,
            task_id=task_id
        )
        assert "id" in start_result
        assert start_result["description"] == "Integration test timer - safe to delete"
        
        # Wait a moment for API consistency
        await asyncio.sleep(3)
        
        # Check that timer is running
        current_running = await tools["toggl_get_current_time_entry"].fn()
        assert "status" not in current_running  # Should have a running entry
        assert current_running["id"] == start_result["id"]
        
        # Stop the timer
        stop_result = await tools["toggl_stop_timer"].fn()
        assert stop_result["id"] == start_result["id"]
        assert stop_result["duration"] > 0  # Should have positive duration when stopped
        
        # Wait a moment for API consistency
        await asyncio.sleep(2)
        
        # Check that no timer is running
        current_after = await tools["toggl_get_current_time_entry"].fn()
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

    async def test_task_management_workflow(self, integration_server: TogglServer):
        """Test complete task management workflow."""
        tools = integration_server.mcp._tool_manager._tools
        
        # Get available projects and find the test project
        projects = await tools["toggl_get_projects"].fn()
        test_project = next((p for p in projects if p["name"] == "Integration Tests"), None)
        if not test_project:
            pytest.fail("Integration Tests project not found - please create a project named 'Integration Tests' in your Toggl workspace")
        
        project_id = test_project["id"]
        
        # Create a test task
        create_result = await tools["toggl_create_task"].fn(
            project_id=project_id,
            name="Test task for integration - safe to delete",
            estimated_hours=2.0
        )
        assert "id" in create_result
        assert create_result["name"] == "Test task for integration - safe to delete"
        assert create_result["estimated_seconds"] == 7200  # 2 hours
        
        task_id = create_result["id"]
        
        # Get the task to verify it was created
        get_result = await tools["toggl_get_task"].fn(project_id=project_id, task_id=task_id)
        assert get_result["id"] == task_id
        assert get_result["name"] == "Test task for integration - safe to delete"
        
        # Update the task
        update_result = await tools["toggl_update_task"].fn(
            project_id=project_id,
            task_id=task_id,
            name="Updated test task",
            estimated_hours=3.0
        )
        assert update_result["id"] == task_id
        assert update_result["name"] == "Updated test task"
        assert update_result["estimated_seconds"] == 10800  # 3 hours
        
        # Get tasks for the project
        tasks_result = await tools["toggl_get_tasks"].fn(project_id=project_id)
        assert isinstance(tasks_result, list)
        # Find our test task in the list
        our_task = next((t for t in tasks_result if t["id"] == task_id), None)
        assert our_task is not None
        assert our_task["name"] == "Updated test task"
        
        # Delete the test task (cleanup)
        delete_result = await tools["toggl_delete_task"].fn(project_id=project_id, task_id=task_id)
        assert delete_result["success"]

        # Wait at end to avoid rate limiting on next test
        await asyncio.sleep(1)

    async def test_client_management_workflow(self, integration_server: TogglServer):
        """Test complete client management workflow."""
        tools = integration_server.mcp._tool_manager._tools

        # Use timestamp to ensure unique client name
        timestamp = datetime.utcnow().isoformat()
        client_name = f"Test Client {timestamp}"

        # Create a test client
        create_result = await tools["toggl_create_client"].fn(
            name=client_name,
            notes="Created by integration test",
            external_reference="TEST-001"
        )
        assert "id" in create_result
        assert create_result["name"] == client_name
        assert create_result["notes"] == "Created by integration test"
        assert create_result["external_reference"] == "TEST-001"

        client_id = create_result["id"]

        # Get the client to verify it was created
        get_result = await tools["toggl_get_client"].fn(client_id=client_id)
        assert get_result["id"] == client_id
        assert get_result["name"] == client_name

        # Update the client
        updated_name = f"Updated {client_name}"
        update_result = await tools["toggl_update_client"].fn(
            client_id=client_id,
            name=updated_name,
            notes="Updated by integration test",
            external_reference="TEST-002"
        )
        assert update_result["id"] == client_id
        assert update_result["name"] == updated_name
        assert update_result["notes"] == "Updated by integration test"
        assert update_result["external_reference"] == "TEST-002"

        # Get all clients and find our test client
        clients_result = await tools["toggl_get_clients"].fn()
        assert isinstance(clients_result, list)
        our_client = next((c for c in clients_result if c["id"] == client_id), None)
        assert our_client is not None
        assert our_client["name"] == updated_name

        # Filter clients by name
        filtered_clients = await tools["toggl_get_clients"].fn(name="Test Client")
        assert isinstance(filtered_clients, list)
        # Our client should appear in filtered results
        found_in_filter = any(c["id"] == client_id for c in filtered_clients)
        assert found_in_filter

        # Delete the test client (cleanup)
        delete_result = await tools["toggl_delete_client"].fn(client_id=client_id)
        assert delete_result["success"]

        # Verify deletion
        verify_result = await tools["toggl_get_client"].fn(client_id=client_id)
        assert "error" in verify_result

        # Wait at end to avoid rate limiting on next test
        await asyncio.sleep(1)

    async def test_project_management_workflow(self, integration_server: TogglServer):
        """Test complete project management workflow."""
        tools = integration_server.mcp._tool_manager._tools

        # Use timestamp to ensure unique project name
        timestamp = datetime.utcnow().isoformat()
        project_name = f"Test Project {timestamp}"

        # Create a test project
        create_result = await tools["toggl_create_project"].fn(
            name=project_name,
            color="#06aaf5",
            billable=True
        )
        assert "id" in create_result
        assert create_result["name"] == project_name
        assert create_result["color"] == "#06aaf5"
        assert create_result["billable"] is True

        project_id = create_result["id"]

        # Get the project to verify it was created
        get_result = await tools["toggl_get_project"].fn(project_id=project_id)
        assert get_result["id"] == project_id
        assert get_result["name"] == project_name

        # Update the project
        updated_name = f"Updated {project_name}"
        update_result = await tools["toggl_update_project"].fn(
            project_id=project_id,
            name=updated_name,
            color="#c56bff",
            billable=False,
            active=False
        )
        assert update_result["id"] == project_id
        assert update_result["name"] == updated_name
        assert update_result["color"] == "#c56bff"
        assert update_result["billable"] is False
        assert update_result["active"] is False

        # Get all projects and find our test project
        projects_result = await tools["toggl_get_projects"].fn()
        assert isinstance(projects_result, list)
        our_project = next((p for p in projects_result if p["id"] == project_id), None)
        assert our_project is not None
        assert our_project["name"] == updated_name

        # Delete the test project (cleanup)
        delete_result = await tools["toggl_delete_project"].fn(project_id=project_id)
        assert delete_result["success"]

        # Verify deletion
        verify_result = await tools["toggl_get_project"].fn(project_id=project_id)
        assert "error" in verify_result

        # Wait at end to avoid rate limiting on next test
        await asyncio.sleep(1)


def test_environment_setup():
    """Test that environment variables are properly configured."""
    api_token = os.getenv("TOGGL_API_TOKEN")
    
    if api_token:
        assert len(api_token) > 10  # Basic sanity check
        assert api_token.strip() == api_token  # No whitespace
    
    workspace_id = os.getenv("TOGGL_WORKSPACE_ID")
    if workspace_id:
        assert workspace_id.isdigit()  # Should be numeric
