"""Pydantic models shared by AI coaching providers and consumers."""
from typing import Any, Literal, Mapping, Optional, Sequence

from pydantic import BaseModel


CoachingRole = Literal["user", "assistant"]
AIErrorCode = Literal["timeout", "throttled", "service_unavailable"]


class CoachingMessage(BaseModel):
    """One user or coach message in a coaching conversation."""

    role: CoachingRole
    content: str


class AICoachError(BaseModel):
    """A provider failure that coaching callers can handle gracefully."""

    code: AIErrorCode
    message: str


class GeneratedOutlineItem(BaseModel):
    """One card topic returned by an AI coach."""

    section: str
    title: str
    description: Optional[str] = None


class GeneratedOutline(BaseModel):
    """A structured deck outline optionally returned with a coach response."""

    items: Sequence[GeneratedOutlineItem]


class CoachingResponse(BaseModel):
    """A coaching answer or a structured provider error."""

    content: Optional[str] = None
    error: Optional[AICoachError] = None
    outline: Optional[GeneratedOutline] = None


class DeckContextResponse(BaseModel):
    """An AI-authored update for the persistent deck context file."""

    context: Optional[dict[str, Any]] = None
    error: Optional[AICoachError] = None


ConversationHistory = Sequence[CoachingMessage]
DeckContext = Mapping[str, Any]