"""Pydantic models for Trello data."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TrelloBoard(BaseModel):
    """Trello board model."""
    id: str
    name: str
    desc: Optional[str] = None
    closed: bool = False
    url: str
    shortUrl: Optional[str] = None


class TrelloList(BaseModel):
    """Trello list model."""
    id: str
    name: str
    closed: bool = False
    idBoard: str
    pos: float


class TrelloCard(BaseModel):
    """Trello card model."""
    id: str
    name: str  # title
    desc: Optional[str] = None  # description
    due: Optional[datetime] = None  # due date
    idList: str  # list ID
    idBoard: str  # board ID
    closed: bool = False
    url: str
    shortUrl: Optional[str] = None
    pos: float
    dateLastActivity: Optional[datetime] = None


class CreateCardRequest(BaseModel):
    """Request model for creating a card."""
    board_id: str = Field(..., description="Board ID")
    list_id: str = Field(..., description="List ID to add the card to")
    title: str = Field(..., description="Card title")
    description: Optional[str] = Field(None, description="Card description")
    due_date: Optional[datetime] = Field(None, description="Due date in ISO 8601 format")


class UpdateCardRequest(BaseModel):
    """Request model for updating a card."""
    card_id: str = Field(..., description="Card ID")
    title: Optional[str] = Field(None, description="New title")
    description: Optional[str] = Field(None, description="New description")
    due_date: Optional[datetime] = Field(None, description="New due date")
    list_id: Optional[str] = Field(None, description="Move to different list")