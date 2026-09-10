"""HTTP models for persisted coaching sessions and deck outlines."""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.ai import AICoachError
from app.models.types import UuidStr


class CoachingMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10_000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        content = value.strip()
        if not content:
            raise ValueError("Message content must not be blank")
        return content


class CoachingMessageResponse(BaseModel):
    id: UuidStr
    session_id: UuidStr
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class CoachingSessionResponse(BaseModel):
    id: UuidStr
    deck_id: UuidStr
    status: Literal["active", "archived"]
    created_at: datetime
    archived_at: Optional[datetime] = None


class CoachingStartResponse(BaseModel):
    session: CoachingSessionResponse
    assistant_message: CoachingMessageResponse


class CoachingSessionDetailResponse(BaseModel):
    session: CoachingSessionResponse
    messages: List[CoachingMessageResponse]


class CoachingSessionListResponse(BaseModel):
    sessions: List[CoachingSessionResponse]
    total: int


class OutlineItemResponse(BaseModel):
    id: UuidStr
    outline_id: UuidStr
    section: str
    title: str
    description: Optional[str]
    position: int
    card_id: Optional[UuidStr] = None


class DeckOutlineResponse(BaseModel):
    id: UuidStr
    deck_id: UuidStr
    generated_at: datetime
    status: Literal["active", "archived"]
    items: List[OutlineItemResponse]


class CoachingMessageResult(BaseModel):
    user_message: CoachingMessageResponse
    assistant_message: Optional[CoachingMessageResponse] = None
    error: Optional[AICoachError] = None
    outline: Optional[DeckOutlineResponse] = None


class DeckOutlineResult(BaseModel):
    outline: Optional[DeckOutlineResponse] = None


class EndCoachingError(BaseModel):
    code: Literal["timeout", "throttled", "service_unavailable", "context_store_unavailable"]
    message: str


class EndCoachingSessionResponse(BaseModel):
    session: CoachingSessionResponse
    context_saved: bool
    error: Optional[EndCoachingError] = None