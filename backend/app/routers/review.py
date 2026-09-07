"""Review session endpoints: due cards and grading."""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import get_current_user
from app.models import CardResponse, DueCardsResponse, FSRSStateResponse, ReviewGradeRequest
from app.services import review_service

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/due", response_model=DueCardsResponse)
async def get_due_cards(
    deck_id: Optional[str] = Query(None, description="Filter to a single deck"),
    user: Dict[str, Any] = Depends(get_current_user),
) -> DueCardsResponse:
    """List all cards due for review, optionally scoped to a single deck."""
    user_id = user["user_id"]
    cards = review_service.get_due_cards(user_id, deck_id)
    return DueCardsResponse(
        cards=[CardResponse(**c) for c in cards],
        total=len(cards),
    )


@router.post("/{card_id}", response_model=FSRSStateResponse)
async def grade_card(
    card_id: str,
    req: ReviewGradeRequest,
    user: Dict[str, Any] = Depends(get_current_user),
) -> FSRSStateResponse:
    """Grade a card during a review session, updating its FSRS state."""
    user_id = user["user_id"]
    fsrs_state = review_service.grade_card(user_id, card_id, req.rating)
    if not fsrs_state:
        raise HTTPException(status_code=404, detail="Card not found")
    return FSRSStateResponse(**fsrs_state)
