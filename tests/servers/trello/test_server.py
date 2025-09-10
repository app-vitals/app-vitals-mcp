"""Tests for Trello MCP Server."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app_vitals_mcp.servers.trello.config import TrelloConfig
from app_vitals_mcp.servers.trello.server import TrelloServer
from app_vitals_mcp.servers.trello.models import TrelloBoard, TrelloList, TrelloCard


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return TrelloConfig(
        api_key="test_api_key",
        token="test_token"
    )


@pytest.fixture
def mock_client():
    """Create a mock Trello client."""
    client = AsyncMock()
    return client


@pytest.fixture
def trello_server(mock_config, mock_client):
    """Create a Trello server with mocked dependencies."""
    with patch('app_vitals_mcp.servers.trello.server.TrelloClient', return_value=mock_client):
        server = TrelloServer(mock_config)
        server.client = mock_client
        return server


@pytest.mark.asyncio
async def test_get_boards(trello_server, mock_client):
    """Test getting all boards."""
    # Mock response
    mock_boards = [
        TrelloBoard(
            id="board1",
            name="Project Board",
            desc="Main project board",
            closed=False,
            url="https://trello.com/b/board1",
            shortUrl="https://trello.com/b/board1"
        ),
        TrelloBoard(
            id="board2",
            name="Personal Board",
            desc="Personal tasks",
            closed=False,
            url="https://trello.com/b/board2",
            shortUrl="https://trello.com/b/board2"
        )
    ]
    mock_client.get_boards.return_value = mock_boards
    
    # Execute
    boards = await trello_server.board_service.get_all_boards()
    
    # Verify
    assert len(boards) == 2
    assert boards[0].name == "Project Board"
    assert boards[1].name == "Personal Board"
    mock_client.get_boards.assert_called_once()


@pytest.mark.asyncio
async def test_get_lists(trello_server, mock_client):
    """Test getting lists in a board."""
    # Mock response
    mock_lists = [
        TrelloList(
            id="list1",
            name="To Do",
            closed=False,
            idBoard="board1",
            pos=1000
        ),
        TrelloList(
            id="list2",
            name="In Progress",
            closed=False,
            idBoard="board1",
            pos=2000
        )
    ]
    mock_client.get_lists.return_value = mock_lists
    
    # Execute
    lists = await trello_server.board_service.get_board_lists("board1")
    
    # Verify
    assert len(lists) == 2
    assert lists[0].name == "To Do"
    assert lists[1].name == "In Progress"
    mock_client.get_lists.assert_called_once_with("board1")


@pytest.mark.asyncio
async def test_create_card(trello_server, mock_client):
    """Test creating a card."""
    # Mock response
    mock_card = TrelloCard(
        id="card1",
        name="Fix bug",
        desc="Fix login issue",
        due=datetime(2024, 12, 31, 23, 59, 59),
        idList="list1",
        idBoard="board1",
        closed=False,
        url="https://trello.com/c/card1",
        shortUrl="https://trello.com/c/card1",
        pos=1000,
        dateLastActivity=datetime.now()
    )
    mock_client.create_card.return_value = mock_card
    
    # Execute
    card = await trello_server.card_service.create_card(
        board_id="board1",
        list_id="list1",
        title="Fix bug",
        description="Fix login issue",
        due_date=datetime(2024, 12, 31, 23, 59, 59)
    )
    
    # Verify
    assert card.name == "Fix bug"
    assert card.desc == "Fix login issue"
    mock_client.create_card.assert_called_once()


@pytest.mark.asyncio
async def test_update_card(trello_server, mock_client):
    """Test updating a card."""
    # Mock response
    mock_card = TrelloCard(
        id="card1",
        name="Fix bug - URGENT",
        desc="Fix login issue ASAP",
        due=datetime(2024, 12, 25, 12, 0, 0),
        idList="list2",
        idBoard="board1",
        closed=False,
        url="https://trello.com/c/card1",
        shortUrl="https://trello.com/c/card1",
        pos=1000,
        dateLastActivity=datetime.now()
    )
    mock_client.update_card.return_value = mock_card
    
    # Execute
    card = await trello_server.card_service.update_card(
        card_id="card1",
        title="Fix bug - URGENT",
        description="Fix login issue ASAP",
        due_date=datetime(2024, 12, 25, 12, 0, 0),
        list_id="list2"
    )
    
    # Verify
    assert card.name == "Fix bug - URGENT"
    assert card.idList == "list2"
    mock_client.update_card.assert_called_once()


@pytest.mark.asyncio
async def test_delete_card(trello_server, mock_client):
    """Test deleting a card."""
    # Mock response
    mock_client.delete_card.return_value = True
    
    # Execute
    result = await trello_server.card_service.delete_card("card1")
    
    # Verify
    assert result is True
    mock_client.delete_card.assert_called_once_with("card1")


@pytest.mark.asyncio
async def test_list_cards(trello_server, mock_client):
    """Test listing cards."""
    # Mock response
    mock_cards = [
        TrelloCard(
            id="card1",
            name="Task 1",
            desc="Description 1",
            due=None,
            idList="list1",
            idBoard="board1",
            closed=False,
            url="https://trello.com/c/card1",
            shortUrl="https://trello.com/c/card1",
            pos=1000,
            dateLastActivity=datetime.now()
        ),
        TrelloCard(
            id="card2",
            name="Task 2",
            desc="Description 2",
            due=None,
            idList="list2",
            idBoard="board1",
            closed=False,
            url="https://trello.com/c/card2",
            shortUrl="https://trello.com/c/card2",
            pos=2000,
            dateLastActivity=datetime.now()
        )
    ]
    mock_client.list_cards.return_value = mock_cards
    
    # Execute
    cards = await trello_server.card_service.list_cards("board1")
    
    # Verify
    assert len(cards) == 2
    assert cards[0].name == "Task 1"
    assert cards[1].name == "Task 2"
    mock_client.list_cards.assert_called_once_with("board1", None)