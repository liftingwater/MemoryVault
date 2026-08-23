"""Card CRUD endpoints."""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user
from app.models import CardCreate, CardUpdate, CardResponse, CardListResponse
from app.services import card_service, deck_service

router = APIRouter(prefix="/decks", tags=["cards"])


@router.post("/{deck_id}/cards", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card(
    deck_id: str,
    req: CardCreate,
    user: Dict[str, Any] = Depends(get_current_user)
) -> CardResponse:
    """Create a new card in a deck."""
    user_id = user["user_id"]
    
    # Verify user owns the deck
    deck = deck_service.get_deck(user_id, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    # Validate card content
    if req.card_type == "front_back":
        if not req.front_md:
            raise HTTPException(status_code=400, detail="front_md is required for front_back cards")
    elif req.card_type == "cloze":
        if not req.cloze_text_md:
            raise HTTPException(status_code=400, detail="cloze_text_md is required for cloze cards")
    
    card = card_service.create_card(
        deck_id=deck_id,
        card_type=req.card_type,
        front_md=req.front_md,
        back_md=req.back_md,
        cloze_text_md=req.cloze_text_md,
        cloze_answer=req.cloze_answer
    )
    if not card:
        raise HTTPException(status_code=500, detail="Failed to create card")
    return CardResponse(**card)


@router.get("/{deck_id}/cards", response_model=CardListResponse)
async def list_cards(
    deck_id: str,
    search: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(get_current_user)
) -> CardListResponse:
    """List cards in a deck with optional search."""
    user_id = user["user_id"]
    
    # Verify user owns the deck
    deck = deck_service.get_deck(user_id, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    cards = card_service.list_cards(deck_id, search)
    return CardListResponse(
        cards=[CardResponse(**c) for c in cards],
        total=len(cards)
    )


@router.put("/cards/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: str,
    req: CardUpdate,
    user: Dict[str, Any] = Depends(get_current_user)
) -> CardResponse:
    """Update a card."""
    card = card_service.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # Verify user owns the deck that contains the card
    deck = deck_service.get_deck(user["user_id"], card["deck_id"])
    if not deck:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    updated = card_service.update_card(
        card_id=card_id,
        card_type=req.card_type,
        front_md=req.front_md,
        back_md=req.back_md,
        cloze_text_md=req.cloze_text_md,
        cloze_answer=req.cloze_answer
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Card not found")
    return CardResponse(**updated)


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> None:
    """Delete a card."""
    card = card_service.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # Verify user owns the deck that contains the card
    deck = deck_service.get_deck(user["user_id"], card["deck_id"])
    if not deck:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    success = card_service.delete_card(card_id)
    if not success:
        raise HTTPException(status_code=404, detail="Card not found")
