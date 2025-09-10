"""Business logic services for Trello operations."""

from typing import List, Optional
from datetime import datetime

from .client import TrelloClient
from .models import TrelloBoard, TrelloList, TrelloCard


class BoardService:
    """Service for board-related operations."""
    
    def __init__(self, client: TrelloClient):
        self.client = client
    
    async def get_all_boards(self) -> List[TrelloBoard]:
        """Get all accessible boards."""
        return await self.client.get_boards()
    
    async def get_board_lists(self, board_id: str) -> List[TrelloList]:
        """Get all lists in a board."""
        return await self.client.get_lists(board_id)


class CardService:
    """Service for card-related operations."""
    
    def __init__(self, client: TrelloClient):
        self.client = client
    
    async def create_card(
        self,
        board_id: str,
        list_id: str,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None
    ) -> TrelloCard:
        """Create a new card in a list."""
        return await self.client.create_card(
            list_id=list_id,
            name=title,
            desc=description,
            due=due_date
        )
    
    async def get_card(self, card_id: str) -> TrelloCard:
        """Get a card by ID."""
        return await self.client.get_card(card_id)
    
    async def list_cards(
        self,
        board_id: str,
        list_id: Optional[str] = None
    ) -> List[TrelloCard]:
        """List all cards on a board or in a specific list."""
        return await self.client.list_cards(board_id, list_id)
    
    async def update_card(
        self,
        card_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
        list_id: Optional[str] = None
    ) -> TrelloCard:
        """Update a card's properties."""
        return await self.client.update_card(
            card_id=card_id,
            name=title,
            desc=description,
            due=due_date,
            idList=list_id
        )
    
    async def delete_card(self, card_id: str) -> bool:
        """Delete a card."""
        return await self.client.delete_card(card_id)