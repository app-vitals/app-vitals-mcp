"""Unit tests for Trello client."""

import pytest
from datetime import datetime
import httpx
import respx

from app_vitals_mcp.servers.trello.client import TrelloClient
from app_vitals_mcp.servers.trello.models import TrelloBoard, TrelloList, TrelloCard


@pytest.fixture
def trello_client():
    """Create a Trello client for testing."""
    return TrelloClient(api_key="test_key", token="test_token")


@pytest.mark.asyncio
@respx.mock
async def test_get_boards(trello_client):
    """Test getting boards."""
    # Mock response
    mock_boards = [
        {
            "id": "board1",
            "name": "Test Board",
            "desc": "Test description",
            "closed": False,
            "url": "https://trello.com/b/board1",
            "shortUrl": "https://trello.com/b/board1"
        }
    ]
    
    route = respx.get("https://api.trello.com/1/members/me/boards").mock(
        return_value=httpx.Response(200, json=mock_boards)
    )
    
    # Execute
    boards = await trello_client.get_boards()
    
    # Verify
    assert len(boards) == 1
    assert boards[0].id == "board1"
    assert boards[0].name == "Test Board"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_get_lists(trello_client):
    """Test getting lists."""
    # Mock response
    mock_lists = [
        {
            "id": "list1",
            "name": "To Do",
            "closed": False,
            "idBoard": "board1",
            "pos": 1000
        },
        {
            "id": "list2",
            "name": "Done",
            "closed": False,
            "idBoard": "board1",
            "pos": 2000
        }
    ]
    
    route = respx.get("https://api.trello.com/1/boards/board1/lists").mock(
        return_value=httpx.Response(200, json=mock_lists)
    )
    
    # Execute
    lists = await trello_client.get_lists("board1")
    
    # Verify
    assert len(lists) == 2
    assert lists[0].id == "list1"
    assert lists[0].name == "To Do"
    assert lists[1].name == "Done"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_create_card(trello_client):
    """Test creating a card."""
    # Mock response
    mock_card = {
        "id": "card1",
        "name": "Test Card",
        "desc": "Test description",
        "due": "2024-12-31T23:59:59.000Z",
        "idList": "list1",
        "idBoard": "board1",
        "closed": False,
        "url": "https://trello.com/c/card1",
        "shortUrl": "https://trello.com/c/card1",
        "pos": 1000,
        "dateLastActivity": "2024-01-01T00:00:00.000Z"
    }
    
    route = respx.post("https://api.trello.com/1/cards").mock(
        return_value=httpx.Response(200, json=mock_card)
    )
    
    # Execute
    card = await trello_client.create_card(
        list_id="list1",
        name="Test Card",
        desc="Test description",
        due=datetime(2024, 12, 31, 23, 59, 59)
    )
    
    # Verify
    assert card.id == "card1"
    assert card.name == "Test Card"
    assert card.desc == "Test description"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_get_card(trello_client):
    """Test getting a card by ID."""
    # Mock response
    mock_card = {
        "id": "card1",
        "name": "Test Card",
        "desc": "Test description",
        "due": None,
        "idList": "list1",
        "idBoard": "board1",
        "closed": False,
        "url": "https://trello.com/c/card1",
        "shortUrl": "https://trello.com/c/card1",
        "pos": 1000,
        "dateLastActivity": "2024-01-01T00:00:00.000Z"
    }
    
    route = respx.get("https://api.trello.com/1/cards/card1").mock(
        return_value=httpx.Response(200, json=mock_card)
    )
    
    # Execute
    card = await trello_client.get_card("card1")
    
    # Verify
    assert card.id == "card1"
    assert card.name == "Test Card"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_update_card(trello_client):
    """Test updating a card."""
    # Mock response
    mock_card = {
        "id": "card1",
        "name": "Updated Card",
        "desc": "Updated description",
        "due": "2024-12-25T12:00:00.000Z",
        "idList": "list2",
        "idBoard": "board1",
        "closed": False,
        "url": "https://trello.com/c/card1",
        "shortUrl": "https://trello.com/c/card1",
        "pos": 1000,
        "dateLastActivity": "2024-01-01T00:00:00.000Z"
    }
    
    route = respx.put("https://api.trello.com/1/cards/card1").mock(
        return_value=httpx.Response(200, json=mock_card)
    )
    
    # Execute
    card = await trello_client.update_card(
        card_id="card1",
        name="Updated Card",
        desc="Updated description",
        due=datetime(2024, 12, 25, 12, 0, 0),
        idList="list2"
    )
    
    # Verify
    assert card.id == "card1"
    assert card.name == "Updated Card"
    assert card.desc == "Updated description"
    assert card.idList == "list2"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_delete_card(trello_client):
    """Test deleting a card."""
    route = respx.delete("https://api.trello.com/1/cards/card1").mock(
        return_value=httpx.Response(200, json={})
    )
    
    # Execute
    result = await trello_client.delete_card("card1")
    
    # Verify
    assert result is True
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_list_cards_by_board(trello_client):
    """Test listing cards by board."""
    # Mock response
    mock_cards = [
        {
            "id": "card1",
            "name": "Card 1",
            "desc": "Description 1",
            "due": None,
            "idList": "list1",
            "idBoard": "board1",
            "closed": False,
            "url": "https://trello.com/c/card1",
            "shortUrl": "https://trello.com/c/card1",
            "pos": 1000,
            "dateLastActivity": "2024-01-01T00:00:00.000Z"
        },
        {
            "id": "card2",
            "name": "Card 2",
            "desc": "Description 2",
            "due": None,
            "idList": "list2",
            "idBoard": "board1",
            "closed": False,
            "url": "https://trello.com/c/card2",
            "shortUrl": "https://trello.com/c/card2",
            "pos": 2000,
            "dateLastActivity": "2024-01-01T00:00:00.000Z"
        }
    ]
    
    route = respx.get("https://api.trello.com/1/boards/board1/cards").mock(
        return_value=httpx.Response(200, json=mock_cards)
    )
    
    # Execute
    cards = await trello_client.list_cards("board1")
    
    # Verify
    assert len(cards) == 2
    assert cards[0].id == "card1"
    assert cards[1].id == "card2"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_list_cards_by_list(trello_client):
    """Test listing cards by list."""
    # Mock response
    mock_cards = [
        {
            "id": "card1",
            "name": "Card 1",
            "desc": "Description 1",
            "due": None,
            "idList": "list1",
            "idBoard": "board1",
            "closed": False,
            "url": "https://trello.com/c/card1",
            "shortUrl": "https://trello.com/c/card1",
            "pos": 1000,
            "dateLastActivity": "2024-01-01T00:00:00.000Z"
        }
    ]
    
    route = respx.get("https://api.trello.com/1/lists/list1/cards").mock(
        return_value=httpx.Response(200, json=mock_cards)
    )
    
    # Execute
    cards = await trello_client.list_cards("board1", list_id="list1")
    
    # Verify
    assert len(cards) == 1
    assert cards[0].id == "card1"
    assert cards[0].idList == "list1"
    assert route.called


@pytest.mark.asyncio
async def test_client_cleanup(trello_client):
    """Test client cleanup."""
    await trello_client.close()
    # Should not raise any errors