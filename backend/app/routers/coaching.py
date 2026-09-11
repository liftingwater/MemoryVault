"""Authenticated API endpoints for persisted AI coaching sessions."""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.models import (
    CoachingMessageCreate, CoachingMessageResult, CoachingSessionDetailResponse,
    CoachingSessionListResponse, CoachingStartResponse, DeckOutlineResult,
    EndCoachingSessionResponse, EndCoachingError,
)
from app.models.ai import CoachingMessage
from app.services.ai_coach import AICoach, get_ai_coach
from app.services.coaching_service import (
    add_message_and_respond, archive_session, get_active_outline, get_history,
    list_sessions, start_session,
)
from app.services.context_store import ContextStore, get_context_store

router = APIRouter(tags=["coaching"])


@router.post("/decks/{deck_id}/coaching/start", response_model=CoachingStartResponse, status_code=status.HTTP_201_CREATED)
async def start_coaching(deck_id: str, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    result = start_session(user["user_id"], deck_id)
    if not result:
        raise HTTPException(status_code=404, detail="Deck not found")
    return result


@router.post("/coaching/{session_id}/message", response_model=CoachingMessageResult)
async def send_message(
    session_id: str, request: CoachingMessageCreate, user: Dict[str, Any] = Depends(get_current_user),
    coach: AICoach = Depends(get_ai_coach), context_store: ContextStore = Depends(get_context_store),
) -> Dict[str, Any]:
    history = get_history(user["user_id"], session_id)
    if not history:
        raise HTTPException(status_code=404, detail="Coaching session not found")
    context: Dict[str, Any] = {}
    if len([message for message in history["messages"] if message["role"] == "user"]) >= 2:
        try:
            context = dict(context_store.load(user["user_id"], history["session"]["deck_id"]))
        except Exception:
            context = {}
    result = add_message_and_respond(user["user_id"], session_id, request.content, context, coach)
    if result is None:
        raise HTTPException(status_code=404, detail="Coaching session not found")
    if result.pop("session_archived", False):
        raise HTTPException(status_code=409, detail="Coaching session is archived")
    return result


@router.get("/decks/{deck_id}/coaching/sessions", response_model=CoachingSessionListResponse)
async def coaching_sessions(deck_id: str, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    sessions = list_sessions(user["user_id"], deck_id)
    if sessions is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    return {"sessions": sessions, "total": len(sessions)}


@router.get("/coaching/{session_id}", response_model=CoachingSessionDetailResponse)
async def coaching_history(session_id: str, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    result = get_history(user["user_id"], session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Coaching session not found")
    return result


@router.post("/coaching/{session_id}/end", response_model=EndCoachingSessionResponse)
async def end_coaching(
    session_id: str, user: Dict[str, Any] = Depends(get_current_user),
    coach: AICoach = Depends(get_ai_coach),
    context_store: ContextStore = Depends(get_context_store),
) -> Dict[str, Any]:
    session = archive_session(user["user_id"], session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Coaching session not found")
    try:
        context = context_store.load(user["user_id"], session["deck_id"])
    except Exception:
        return _context_store_error(session)
    history = get_history(user["user_id"], session_id)
    messages = [
        CoachingMessage(role=message["role"], content=message["content"])
        for message in history["messages"]
    ] if history else []
    try:
        response = coach.generate_context(messages, context)
    except Exception:
        return {
            "session": session,
            "context_saved": False,
            "error": EndCoachingError(
                code="service_unavailable",
                message="The AI service is unavailable. Please try again later.",
            ),
        }
    if response.error or response.context is None:
        error = response.error or EndCoachingError(
            code="service_unavailable",
            message="The AI service did not return a deck context update.",
        )
        return {"session": session, "context_saved": False, "error": error}
    try:
        updated_context = dict(context)
        updated_context.update(response.context)
        context_store.save(user["user_id"], session["deck_id"], updated_context)
    except Exception:
        return _context_store_error(session)
    return {"session": session, "context_saved": True}


def _context_store_error(session: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "session": session,
        "context_saved": False,
        "error": EndCoachingError(
            code="context_store_unavailable",
            message="Deck context could not be saved.",
        ),
    }


@router.get("/decks/{deck_id}/outline", response_model=DeckOutlineResult)
async def deck_outline(deck_id: str, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    result = get_active_outline(user["user_id"], deck_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    return result