"""Card CRUD endpoints."""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user
from app.models import CardCreate, CardUpdate, CardResponse, CardListResponse
from app.services import card_service

router = APIRouter(tags=["cards"])


@router.post("/decks/{deck_id}/cards", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card(
    deck_id: str,
    req: CardCreate,
    user: Dict[str, Any] = Depends(get_current_user)
) -> CardResponse:
    """Create a new card in a deck."""
    user_id = user["user_id"]
    card = card_service.create_card(
        user_id=user_id,
        deck_id=deck_id,
        card_type=req.card_type,
        front_md=req.front_md,
        back_md=req.back_md,
        cloze_text_md=req.cloze_text_md,
        cloze_answer=req.cloze_answer,
    )
    if not card:
        raise HTTPException(status_code=404, detail="Deck not found")
    return CardResponse(**card)


@router.get("/decks/{deck_id}/cards", response_model=CardListResponse)
async def list_cards(
    deck_id: str,
    search: Optional[str] = Query(None, description="Search query"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> CardListResponse:
    """List cards in a deck with optional search."""
    user_id = user["user_id"]
    cards = card_service.list_cards(user_id, deck_id, search)
    return CardListResponse(
        cards=[CardResponse(**c) for c in cards],
        total=len(cards)
    )


@router.get("/cards/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> CardResponse:
    """Get a single card by ID."""
    user_id = user["user_id"]
    card = card_service.get_card(user_id, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return CardResponse(**card)


@router.put("/cards/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: str,
    req: CardUpdate,
    user: Dict[str, Any] = Depends(get_current_user)
) -> CardResponse:
    """Update a card."""
    user_id = user["user_id"]
    card = card_service.update_card(
        user_id=user_id,
        card_id=card_id,
        front_md=req.front_md,
        back_md=req.back_md,
        cloze_text_md=req.cloze_text_md,
        cloze_answer=req.cloze_answer,
    )
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return CardResponse(**card)


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> None:
    """Delete a card."""
    user_id = user["user_id"]
    success = card_service.delete_card(user_id, card_id)
    if not success:
        raise HTTPException(status_code=404, detail="Card not found")
