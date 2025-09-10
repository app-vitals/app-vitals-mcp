"""Integration tests for Trello MCP Server.

These tests require real Trello API credentials and will interact with
an "Integration Testing" board in your Trello account.
"""

import os
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone

from app_vitals_mcp.servers.trello.config import TrelloConfig
from app_vitals_mcp.servers.trello.client import TrelloClient


@pytest.fixture
def real_trello_config():
    """Get real Trello configuration from environment."""
    api_key = os.getenv("TRELLO_API_KEY")
    token = os.getenv("TRELLO_TOKEN")
    
    if not api_key or not token:
        pytest.skip("TRELLO_API_KEY and TRELLO_TOKEN environment variables required for integration tests")
    
    return TrelloConfig(api_key=api_key, token=token)


@pytest_asyncio.fixture
async def real_trello_client(real_trello_config):
    """Create real Trello client for integration tests."""
    client = TrelloClient(real_trello_config.api_key, real_trello_config.token)
    yield client
    await client.close()


@pytest_asyncio.fixture
async def integration_board(real_trello_client):
    """Get or create the Integration Testing board."""
    boards = await real_trello_client.get_boards()
    
    # Look for existing integration testing board (case insensitive)
    for board in boards:
        if "integration" in board.name.lower() and "test" in board.name.lower():
            return board
    
    # If not found, we'll need to create it (not implemented in client yet)
    pytest.skip("Integration Testing board not found. Please create a board with 'integration' and 'test' in the name.")


@pytest_asyncio.fixture
async def test_lists(real_trello_client, integration_board):
    """Get lists from the integration testing board."""
    lists = await real_trello_client.get_lists(integration_board.id)
    
    # Create a case-insensitive mapping
    list_names = {}
    todo_list = None
    done_list = None
    
    for lst in lists:
        if "todo" in lst.name.lower() or "to do" in lst.name.lower():
            todo_list = lst
            list_names["To Do"] = lst
        elif "done" in lst.name.lower():
            done_list = lst
            list_names["Done"] = lst
    
    if not todo_list or not done_list:
        available_lists = [lst.name for lst in lists]
        pytest.skip(f"Integration board must have 'todo' and 'done' lists. Found: {available_lists}")
    
    return list_names


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_board_exists(integration_board):
    """Test that we can access the integration testing board."""
    assert integration_board is not None
    assert "integration" in integration_board.name.lower()
    assert "test" in integration_board.name.lower()
    assert integration_board.id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_lists_exist(test_lists):
    """Test that required lists exist."""
    assert "To Do" in test_lists
    assert "Done" in test_lists


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_card_lifecycle(real_trello_client, integration_board, test_lists):
    """Test full card lifecycle: create, read, update, move, delete."""
    todo_list = test_lists["To Do"]
    done_list = test_lists["Done"]
    
    # Create a card
    test_title = f"Test Card {datetime.now().isoformat()}"
    test_desc = "This is a test card created by integration tests"
    due_date = datetime.now(timezone.utc) + timedelta(days=7)
    
    created_card = await real_trello_client.create_card(
        list_id=todo_list.id,
        name=test_title,
        desc=test_desc,
        due=due_date
    )
    
    assert created_card.id
    assert created_card.name == test_title
    assert created_card.desc == test_desc
    assert created_card.idList == todo_list.id
    
    try:
        # Read the card
        fetched_card = await real_trello_client.get_card(created_card.id)
        assert fetched_card.id == created_card.id
        assert fetched_card.name == test_title
        
        # Update the card
        updated_title = f"Updated {test_title}"
        updated_desc = "Updated description"
        updated_card = await real_trello_client.update_card(
            card_id=created_card.id,
            name=updated_title,
            desc=updated_desc
        )
        
        assert updated_card.name == updated_title
        assert updated_card.desc == updated_desc
        
        # Move card to Done list
        moved_card = await real_trello_client.update_card(
            card_id=created_card.id,
            idList=done_list.id
        )
        
        assert moved_card.idList == done_list.id
        
        # List cards in Done list
        done_cards = await real_trello_client.list_cards(
            board_id=integration_board.id,
            list_id=done_list.id
        )
        
        card_ids = [card.id for card in done_cards]
        assert created_card.id in card_ids
        
    finally:
        # Clean up - delete the card
        await real_trello_client.delete_card(created_card.id)
        
        # Verify deletion
        all_cards = await real_trello_client.list_cards(integration_board.id)
        card_ids = [card.id for card in all_cards]
        assert created_card.id not in card_ids


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_due_dates(real_trello_client, test_lists):
    """Test creating and updating cards with due dates."""
    todo_list = test_lists["To Do"]
    
    # Create card with due date
    due_date = datetime.now(timezone.utc) + timedelta(days=3)
    card = await real_trello_client.create_card(
        list_id=todo_list.id,
        name=f"Due Date Test {datetime.now().isoformat()}",
        desc="Testing due dates",
        due=due_date
    )
    
    assert card.due is not None
    
    try:
        # Update due date
        new_due_date = datetime.now(timezone.utc) + timedelta(days=5)
        updated_card = await real_trello_client.update_card(
            card_id=card.id,
            due=new_due_date
        )
        
        assert updated_card.due is not None
        
        # Remove due date
        no_due_card = await real_trello_client.update_card(
            card_id=card.id,
            due=None
        )
        
        # Note: Trello API might still return a due date field, but it should be None or removed
        
    finally:
        # Clean up
        await real_trello_client.delete_card(card.id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_list_all_cards(real_trello_client, integration_board, test_lists):
    """Test listing all cards on a board."""
    todo_list = test_lists["To Do"]
    
    # Create multiple test cards
    created_cards = []
    for i in range(3):
        card = await real_trello_client.create_card(
            list_id=todo_list.id,
            name=f"Bulk Test Card {i} - {datetime.now().isoformat()}",
            desc=f"Test card number {i}"
        )
        created_cards.append(card)
    
    try:
        # List all cards on the board
        all_cards = await real_trello_client.list_cards(integration_board.id)
        
        # Check that our cards are in the list
        card_ids = [card.id for card in all_cards]
        for created_card in created_cards:
            assert created_card.id in card_ids
        
        # List cards in specific list
        todo_cards = await real_trello_client.list_cards(
            board_id=integration_board.id,
            list_id=todo_list.id
        )
        
        todo_card_ids = [card.id for card in todo_cards]
        for created_card in created_cards:
            assert created_card.id in todo_card_ids
        
    finally:
        # Clean up all created cards
        for card in created_cards:
            await real_trello_client.delete_card(card.id)