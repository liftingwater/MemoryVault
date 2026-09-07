"""Pydantic models for the FSRS review flow and dashboard."""
from typing import Optional
from datetime import date
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore
from pydantic import BaseModel, Field

from app.models.card import CardListResponse
from app.models.types import UuidStr

# Binary grading only for MVP (see SPEC.md "Review grading evolution").
Rating = Literal["got_it", "need_review"]


class ReviewGradeRequest(BaseModel):
    """Request body for grading a card during a review session."""
    rating: Rating = Field(..., description="got_it or need_review")


class FSRSStateResponse(BaseModel):
    """Response model for a card's FSRS scheduling state after grading."""
    card_id: UuidStr
    stability: float
    difficulty: float
    due_date: date
    last_review: Optional[date]
    reps: int
    lapses: int
    state: str

    class Config:
        from_attributes = True


# Reuse CardResponse's shape for the due queue: reviewers need the same
# renderable content (front/back/cloze) as the card editor/list views.
DueCardsResponse = CardListResponse
