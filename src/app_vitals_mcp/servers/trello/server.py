"""Trello MCP Server implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from fastmcp import FastMCP

from .config import TrelloConfig
from .client import TrelloClient
from .services import BoardService, CardService


class TrelloServer:
    """Trello MCP Server with layered architecture."""
    
    def __init__(self, config: TrelloConfig):
        self.config = config
        self.client = TrelloClient(config.api_key, config.token)
        self.mcp: FastMCP = FastMCP("Trello Card Management Server")
        
        # Initialize services
        self.board_service = BoardService(self.client)
        self.card_service = CardService(self.client)
        
        self._setup_tools()
    
    def _setup_tools(self):
        """Set up MCP tools organized by category."""
        self._setup_board_tools()
        self._setup_card_tools()
    
    def _setup_board_tools(self):
        """Set up board-related tools."""
        
        @self.mcp.tool()
        async def trello_get_boards() -> List[Dict[str, Any]]:
            """List all accessible Trello boards.
            
            Returns:
                List of boards with their IDs and names
            """
            boards = await self.board_service.get_all_boards()
            return [board.model_dump() for board in boards]
        
        @self.mcp.tool()
        async def trello_get_lists(board_id: str) -> List[Dict[str, Any]]:
            """Get all lists in a Trello board.
            
            Args:
                board_id: The board ID
                
            Returns:
                List of lists with their IDs and names
            """
            lists = await self.board_service.get_board_lists(board_id)
            return [list_data.model_dump() for list_data in lists]
    
    def _setup_card_tools(self):
        """Set up card-related tools."""
        
        @self.mcp.tool()
        async def trello_create_card(
            board_id: str,
            list_id: str,
            title: str,
            description: Optional[str] = None,
            due_date: Optional[str] = None
        ) -> Dict[str, Any]:
            """Create a new Trello card.
            
            Args:
                board_id: The board ID
                list_id: The list ID to add the card to
                title: Card title
                description: Optional card description
                due_date: Optional due date in ISO 8601 format (e.g., "2024-12-31T23:59:59Z")
                
            Returns:
                Created card object with ID and details
            """
            due_datetime = None
            if due_date:
                due_datetime = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            
            card = await self.card_service.create_card(
                board_id=board_id,
                list_id=list_id,
                title=title,
                description=description,
                due_date=due_datetime
            )
            return card.model_dump()
        
        @self.mcp.tool()
        async def trello_get_card(card_id: str) -> Dict[str, Any]:
            """Get a Trello card by ID.
            
            Args:
                card_id: The card ID
                
            Returns:
                Card object with all properties
            """
            card = await self.card_service.get_card(card_id)
            return card.model_dump()
        
        @self.mcp.tool()
        async def trello_list_cards(
            board_id: str,
            list_id: Optional[str] = None
        ) -> List[Dict[str, Any]]:
            """List Trello cards on a board or in a specific list.
            
            Args:
                board_id: The board ID
                list_id: Optional list ID to filter cards
                
            Returns:
                List of card objects
            """
            cards = await self.card_service.list_cards(board_id, list_id)
            return [card.model_dump() for card in cards]
        
        @self.mcp.tool()
        async def trello_update_card(
            card_id: str,
            title: Optional[str] = None,
            description: Optional[str] = None,
            due_date: Optional[str] = None,
            list_id: Optional[str] = None
        ) -> Dict[str, Any]:
            """Update a Trello card.
            
            Args:
                card_id: The card ID
                title: Optional new title
                description: Optional new description
                due_date: Optional new due date in ISO 8601 format (use "null" to remove)
                list_id: Optional list ID to move the card to
                
            Returns:
                Updated card object
            """
            due_datetime = None
            if due_date:
                if due_date.lower() != "null":
                    due_datetime = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            
            card = await self.card_service.update_card(
                card_id=card_id,
                title=title,
                description=description,
                due_date=due_datetime,
                list_id=list_id
            )
            return card.model_dump()
        
        @self.mcp.tool()
        async def trello_delete_card(card_id: str) -> Dict[str, str]:
            """Delete a Trello card.
            
            Args:
                card_id: The card ID
                
            Returns:
                Success confirmation
            """
            success = await self.card_service.delete_card(card_id)
            return {"status": "success" if success else "failed", "card_id": card_id}
    
    async def run(self):
        """Run the MCP server."""
        await self.mcp.run()
    
    async def cleanup(self):
        """Clean up resources."""
        await self.client.close()