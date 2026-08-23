"""Pydantic models for Card CRUD operations."""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CardCreate(BaseModel):
    """Request model for creating a card."""
    card_type: str = Field(..., pattern="^(front_back|cloze)$")
    # front_back fields
    front_md: Optional[str] = Field(None, min_length=1)
    back_md: Optional[str] = None
    # cloze fields
    cloze_text_md: Optional[str] = Field(None, min_length=1)
    cloze_answer: Optional[str] = None


class CardUpdate(BaseModel):
    """Request model for updating a card."""
    card_type: Optional[str] = Field(None, pattern="^(front_back|cloze)$")
    front_md: Optional[str] = Field(None, min_length=1)
    back_md: Optional[str] = None
    cloze_text_md: Optional[str] = Field(None, min_length=1)
    cloze_answer: Optional[str] = None


class CardResponse(BaseModel):
    """Response model for a single card."""
    id: str
    deck_id: str
    card_type: str
    front_md: Optional[str]
    back_md: Optional[str]
    cloze_text_md: Optional[str]
    cloze_answer: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CardListResponse(BaseModel):
    """Response model for listing cards."""
    cards: List[CardResponse]
    total: int
