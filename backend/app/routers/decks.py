"""Deck CRUD endpoints."""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.models import DeckCreate, DeckUpdate, DeckResponse, DeckListResponse
from app.services import deck_service

router = APIRouter(prefix="/decks", tags=["decks"])


@router.post("", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
async def create_deck(
    req: DeckCreate,
    user: Dict[str, Any] = Depends(get_current_user)
) -> DeckResponse:
    """Create a new deck."""
    user_id = user["user_id"]
    deck = deck_service.create_deck(
        user_id=user_id,
        name=req.name,
        description=req.description,
        tags=req.tags
    )
    if not deck:
        raise HTTPException(status_code=500, detail="Failed to create deck")
    return DeckResponse(**deck)


@router.get("", response_model=DeckListResponse)
async def list_decks(
    user: Dict[str, Any] = Depends(get_current_user)
) -> DeckListResponse:
    """List all decks for the user."""
    user_id = user["user_id"]
    decks = deck_service.list_decks(user_id)
    return DeckListResponse(
        decks=[DeckResponse(**d) for d in decks],
        total=len(decks)
    )


@router.get("/{deck_id}", response_model=DeckResponse)
async def get_deck(
    deck_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> DeckResponse:
    """Get a single deck by ID."""
    user_id = user["user_id"]
    deck = deck_service.get_deck(user_id, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return DeckResponse(**deck)


@router.put("/{deck_id}", response_model=DeckResponse)
async def update_deck(
    deck_id: str,
    req: DeckUpdate,
    user: Dict[str, Any] = Depends(get_current_user)
) -> DeckResponse:
    """Update a deck."""
    user_id = user["user_id"]
    deck = deck_service.update_deck(
        user_id=user_id,
        deck_id=deck_id,
        name=req.name,
        description=req.description,
        tags=req.tags
    )
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return DeckResponse(**deck)


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deck(
    deck_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> None:
    """Delete a deck and cascade to all related data."""
    user_id = user["user_id"]
    success = deck_service.delete_deck(user_id, deck_id)
    if not success:
        raise HTTPException(status_code=404, detail="Deck not found")
