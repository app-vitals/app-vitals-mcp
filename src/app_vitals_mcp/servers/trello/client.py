"""Trello API client."""

from typing import List, Optional, Dict
from datetime import datetime
import httpx

from .models import TrelloBoard, TrelloList, TrelloCard


class TrelloClient:
    """Client for interacting with Trello API."""
    
    BASE_URL = "https://api.trello.com/1"
    
    def __init__(self, api_key: str, token: str):
        """Initialize Trello client with API credentials."""
        self.api_key = api_key
        self.token = token
        self.client = httpx.AsyncClient()
    
    def _get_auth_params(self) -> Dict[str, str]:
        """Get authentication parameters for requests."""
        return {
            "key": self.api_key,
            "token": self.token
        }
    
    async def get_boards(self) -> List[TrelloBoard]:
        """Get all boards for the authenticated user."""
        response = await self.client.get(
            f"{self.BASE_URL}/members/me/boards",
            params=self._get_auth_params()
        )
        response.raise_for_status()
        return [TrelloBoard(**board) for board in response.json()]
    
    async def get_lists(self, board_id: str) -> List[TrelloList]:
        """Get all lists in a board."""
        response = await self.client.get(
            f"{self.BASE_URL}/boards/{board_id}/lists",
            params=self._get_auth_params()
        )
        response.raise_for_status()
        return [TrelloList(**list_data) for list_data in response.json()]
    
    async def create_card(
        self,
        list_id: str,
        name: str,
        desc: Optional[str] = None,
        due: Optional[datetime] = None
    ) -> TrelloCard:
        """Create a new card."""
        params = {
            **self._get_auth_params(),
            "idList": list_id,
            "name": name
        }
        
        if desc:
            params["desc"] = desc
        
        if due:
            params["due"] = due.isoformat()
        
        response = await self.client.post(
            f"{self.BASE_URL}/cards",
            params=params
        )
        response.raise_for_status()
        return TrelloCard(**response.json())
    
    async def get_card(self, card_id: str) -> TrelloCard:
        """Get a card by ID."""
        response = await self.client.get(
            f"{self.BASE_URL}/cards/{card_id}",
            params=self._get_auth_params()
        )
        response.raise_for_status()
        return TrelloCard(**response.json())
    
    async def update_card(
        self,
        card_id: str,
        name: Optional[str] = None,
        desc: Optional[str] = None,
        due: Optional[datetime] = None,
        idList: Optional[str] = None
    ) -> TrelloCard:
        """Update a card."""
        params = self._get_auth_params()
        
        if name is not None:
            params["name"] = name
        
        if desc is not None:
            params["desc"] = desc
        
        if due is not None:
            params["due"] = due.isoformat() if due else "null"
        
        if idList is not None:
            params["idList"] = idList
        
        response = await self.client.put(
            f"{self.BASE_URL}/cards/{card_id}",
            params=params
        )
        response.raise_for_status()
        return TrelloCard(**response.json())
    
    async def delete_card(self, card_id: str) -> bool:
        """Delete a card."""
        response = await self.client.delete(
            f"{self.BASE_URL}/cards/{card_id}",
            params=self._get_auth_params()
        )
        response.raise_for_status()
        return True
    
    async def list_cards(
        self,
        board_id: str,
        list_id: Optional[str] = None
    ) -> List[TrelloCard]:
        """List cards on a board or in a specific list."""
        if list_id:
            url = f"{self.BASE_URL}/lists/{list_id}/cards"
        else:
            url = f"{self.BASE_URL}/boards/{board_id}/cards"
        
        response = await self.client.get(
            url,
            params=self._get_auth_params()
        )
        response.raise_for_status()
        return [TrelloCard(**card) for card in response.json()]
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()