"""Persistence and workflow rules for deck coaching sessions."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, cast
import uuid

from app.database import get_db
from app.models.ai import (
    AICoachError,
    CoachingMessage,
    CoachingResponse,
    DeckContext,
    GeneratedOutline,
)

GOAL_QUESTION = "What is your learning goal for this deck?"
KNOWLEDGE_QUESTION = "What do you already know about this subject?"
TIME_QUESTION = "How much time can you commit to studying each week?"
_INTAKE_FOLLOW_UPS = (KNOWLEDGE_QUESTION, TIME_QUESTION)
_SESSION_COLUMNS = "id, deck_id, status, created_at, archived_at"
_MESSAGE_COLUMNS = "id, session_id, role, content, created_at"


def start_session(user_id: str, deck_id: str) -> Optional[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    session_id = str(uuid.uuid4())
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM decks WHERE id = %s AND user_id = %s FOR UPDATE",
                (deck_id, user_id),
            )
            if not cur.fetchone():
                return None
            cur.execute(
                "UPDATE coaching_sessions SET status = 'archived', archived_at = %s "
                "WHERE deck_id = %s AND status = 'active'", (now, deck_id)
            )
            cur.execute(
                f"INSERT INTO coaching_sessions ({_SESSION_COLUMNS}) VALUES (%s, %s, %s, %s, %s) "
                f"RETURNING {_SESSION_COLUMNS}", (session_id, deck_id, "active", now, None)
            )
            session = _row_to_dict(cur.fetchone(), cur.description)
            message = _insert_message(cur, session_id, "assistant", GOAL_QUESTION, now)
            return {"session": session, "assistant_message": message}


def get_session(user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT s.{_SESSION_COLUMNS.replace(', ', ', s.')} FROM coaching_sessions s "
                "JOIN decks d ON d.id = s.deck_id WHERE s.id = %s AND d.user_id = %s",
                (session_id, user_id),
            )
            row = cur.fetchone()
            return _row_to_dict(row, cur.description) if row else None


def list_sessions(user_id: str, deck_id: str) -> Optional[List[Dict[str, Any]]]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM decks WHERE id = %s AND user_id = %s", (deck_id, user_id))
            if not cur.fetchone():
                return None
            cur.execute(
                f"SELECT {_SESSION_COLUMNS} FROM coaching_sessions WHERE deck_id = %s "
                "ORDER BY created_at DESC", (deck_id,)
            )
            return [_row_to_dict(row, cur.description) for row in cur.fetchall()]


def get_history(user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    session = get_session(user_id, session_id)
    if not session:
        return None
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {_MESSAGE_COLUMNS} FROM coaching_messages WHERE session_id = %s "
                "ORDER BY created_at ASC, id ASC", (session_id,)
            )
            return {"session": session, "messages": [_row_to_dict(row, cur.description) for row in cur.fetchall()]}


def add_message_and_respond(
    user_id: str, session_id: str, content: str, context: DeckContext, coach: Any,
) -> Optional[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT s.{_SESSION_COLUMNS.replace(', ', ', s.')} FROM coaching_sessions s "
                "JOIN decks d ON d.id = s.deck_id "
                "WHERE s.id = %s AND d.user_id = %s FOR UPDATE",
                (session_id, user_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            session = _row_to_dict(row, cur.description)
            if session["status"] != "active":
                return {"session_archived": True}
            user_message = _insert_message(cur, session_id, "user", content, now)
            cur.execute(
                "SELECT role, content FROM coaching_messages WHERE session_id = %s "
                "ORDER BY created_at ASC, id ASC",
                (session_id,),
            )
            rows = cur.fetchall()
            user_count = sum(1 for role, _ in rows if role == "user")
            if user_count <= len(_INTAKE_FOLLOW_UPS):
                assistant = _insert_message(
                    cur,
                    session_id,
                    "assistant",
                    _INTAKE_FOLLOW_UPS[user_count - 1],
                    now + timedelta(microseconds=1),
                )
                return {"user_message": user_message, "assistant_message": assistant}
    response = _generate_safely(coach, [CoachingMessage(role=r, content=c) for r, c in rows], context)
    if response.error:
        return {"user_message": user_message, "error": response.error}
    if not response.content:
        return {"user_message": user_message, "error": {"code": "service_unavailable", "message": "The AI service returned no response."}}
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {_SESSION_COLUMNS} FROM coaching_sessions WHERE id = %s FOR UPDATE",
                (session_id,),
            )
            row = cur.fetchone()
            if not row or _row_to_dict(row, cur.description)["status"] != "active":
                return {"session_archived": True}
            assistant = _insert_message(cur, session_id, "assistant", response.content, datetime.now(timezone.utc))
            outline = (
                create_outline(cur, session["deck_id"], response.outline)
                if response.outline and user_count > len(_INTAKE_FOLLOW_UPS) + 1
                else None
            )
    return {"user_message": user_message, "assistant_message": assistant, "outline": outline}


def archive_session(user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    session = get_session(user_id, session_id)
    if not session:
        return None
    if session["status"] == "archived":
        return session
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE coaching_sessions SET status = 'archived', archived_at = %s WHERE id = %s RETURNING {_SESSION_COLUMNS}",
                (datetime.now(timezone.utc), session_id),
            )
            return _row_to_dict(cur.fetchone(), cur.description)


def get_active_outline(user_id: str, deck_id: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM decks WHERE id = %s AND user_id = %s", (deck_id, user_id))
            if not cur.fetchone():
                return None
            cur.execute(
                "SELECT id, deck_id, generated_at, status FROM deck_outlines WHERE deck_id = %s AND status = 'active' "
                "ORDER BY generated_at DESC LIMIT 1", (deck_id,)
            )
            row = cur.fetchone()
            if not row:
                return {"outline": None}
            outline = _row_to_dict(row, cur.description)
            cur.execute(
                "SELECT id, outline_id, section, title, description, position, card_id FROM outline_items "
                "WHERE outline_id = %s ORDER BY position ASC", (outline["id"],)
            )
            outline["items"] = [_row_to_dict(item, cur.description) for item in cur.fetchall()]
            return {"outline": outline}


def create_outline(cur: Any, deck_id: str, generated: GeneratedOutline) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    outline_id = str(uuid.uuid4())
    cur.execute("UPDATE deck_outlines SET status = 'archived' WHERE deck_id = %s AND status = 'active'", (deck_id,))
    cur.execute(
        "INSERT INTO deck_outlines (id, deck_id, generated_at, status) VALUES (%s, %s, %s, %s) "
        "RETURNING id, deck_id, generated_at, status", (outline_id, deck_id, now, "active")
    )
    outline = _row_to_dict(cur.fetchone(), cur.description)
    items: List[Dict[str, Any]] = []
    for position, item in enumerate(generated.items):
        item_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO outline_items (id, outline_id, section, title, description, position, card_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id, outline_id, section, title, description, position, card_id",
            (item_id, outline_id, item.section, item.title, item.description, position, None),
        )
        items.append(_row_to_dict(cur.fetchone(), cur.description))
    outline["items"] = items
    return outline


def _insert_message(cur: Any, session_id: str, role: str, content: str, now: datetime) -> Dict[str, Any]:
    cur.execute(
        f"INSERT INTO coaching_messages ({_MESSAGE_COLUMNS}) VALUES (%s, %s, %s, %s, %s) RETURNING {_MESSAGE_COLUMNS}",
        (str(uuid.uuid4()), session_id, role, content, now),
    )
    return _row_to_dict(cur.fetchone(), cur.description)


def _generate_safely(coach: Any, history: Sequence[CoachingMessage], context: DeckContext) -> CoachingResponse:
    try:
        return cast(CoachingResponse, coach.generate_response(history, context))
    except Exception:
        return CoachingResponse(
            error=AICoachError(
                code="service_unavailable",
                message="The AI service is unavailable. Please try again later.",
            )
        )


def _row_to_dict(row: Any, description: Any) -> Dict[str, Any]:
    return dict(zip([column[0] for column in description], row))