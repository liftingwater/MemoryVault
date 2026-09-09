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


class CoachingResponse(BaseModel):
    """A coaching answer or a structured provider error."""

    content: Optional[str] = None
    error: Optional[AICoachError] = None


ConversationHistory = Sequence[CoachingMessage]
DeckContext = Mapping[str, Any]