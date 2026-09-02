"""Pydantic models for Card CRUD operations."""
from typing import List, Optional, Any
from datetime import datetime
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore
from pydantic import BaseModel, Field, model_validator


class CardCreate(BaseModel):
    """Request model for creating a card."""
    card_type: Literal["front_back", "cloze"] = Field(..., description="Card type: front_back or cloze")
    front_md: str = Field(..., min_length=1, description="Front content (markdown)")
    back_md: Optional[str] = Field(None, description="Back content for front_back cards (markdown)")
    cloze_text_md: Optional[str] = Field(None, description="Full text for cloze cards (markdown with cloze markers)")
    cloze_answer: Optional[str] = Field(None, description="Expected answer for cloze cards")

    @model_validator(mode="after")
    def validate_card_type(self) -> "CardCreate":
        """Validate that required fields are present for card type."""
        if self.card_type == "front_back" and not self.back_md:
            raise ValueError("back_md is required for front_back cards")
        if self.card_type == "cloze" and not self.cloze_text_md:
            raise ValueError("cloze_text_md is required for cloze cards")
        return self


class CardUpdate(BaseModel):
    """Request model for updating a card."""
    front_md: Optional[str] = Field(None, min_length=1, description="Front content (markdown)")
    back_md: Optional[str] = Field(None, description="Back content for front_back cards")
    cloze_text_md: Optional[str] = Field(None, description="Full text for cloze cards")
    cloze_answer: Optional[str] = Field(None, description="Expected answer for cloze cards")


class CardResponse(BaseModel):
    """Response model for a single card."""
    id: str
    deck_id: str
    card_type: str
    front_md: str
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
