"""Pydantic models for Deck CRUD operations."""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DeckCreate(BaseModel):
    """Request model for creating a deck."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: List[str] = Field(default_factory=list)


class DeckUpdate(BaseModel):
    """Request model for updating a deck."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None


class DeckResponse(BaseModel):
    """Response model for a single deck."""
    id: str
    name: str
    description: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    card_count: int = 0  # Will be populated from database

    class Config:
        from_attributes = True


class DeckListResponse(BaseModel):
    """Response model for listing decks."""
    decks: List[DeckResponse]
    total: int
