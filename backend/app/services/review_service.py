"""Database service for the review flow (due cards, grading, dashboard)."""
from typing import Any, Dict, List, Optional
from datetime import date, datetime, timedelta
import uuid

from app.database import get_db
from app.services import fsrs_service


def get_due_cards(user_id: str, deck_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all of the user's cards that are due for review, optionally
    scoped to a single deck. Ordered so the most overdue cards come first.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT c.id, c.deck_id, c.card_type, c.front_md, c.back_md,
                       c.cloze_text_md, c.cloze_answer, c.created_at, c.updated_at
                FROM cards c
                JOIN fsrs_states f ON f.card_id = c.id
                JOIN decks d ON c.deck_id = d.id
                WHERE d.user_id = %s AND f.due_date <= CURRENT_DATE
            """
            params: List[Any] = [user_id]
            if deck_id:
                query += " AND c.deck_id = %s"
                params.append(deck_id)
            query += " ORDER BY f.due_date ASC, c.created_at ASC"

            cur.execute(query, params)
            rows = cur.fetchall()
            return [_row_to_dict(row, cur.description) for row in rows]


def grade_card(user_id: str, card_id: str, rating: str) -> Optional[Dict[str, Any]]:
    """Grade a card, updating its FSRSState and appending a ReviewLog entry.

    Returns the updated FSRSState row, or None if the card doesn't exist or
    isn't owned by the user.
    """
    now = datetime.utcnow()

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT f.card_id, f.stability, f.difficulty, f.due_date,
                       f.last_review, f.reps, f.lapses, f.state
                FROM fsrs_states f
                JOIN cards c ON f.card_id = c.id
                JOIN decks d ON c.deck_id = d.id
                WHERE f.card_id = %s AND d.user_id = %s
                """,
                (card_id, user_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            fsrs_row = _row_to_dict(row, cur.description)

            updated = fsrs_service.apply_review(fsrs_row, rating, now)

            cur.execute(
                """
                UPDATE fsrs_states
                SET stability = %s, difficulty = %s, due_date = %s,
                    last_review = %s, reps = %s, lapses = %s, state = %s
                WHERE card_id = %s
                """,
                (
                    updated["stability"], updated["difficulty"], updated["due_date"],
                    updated["last_review"], updated["reps"], updated["lapses"],
                    updated["state"], card_id,
                ),
            )

            cur.execute(
                """
                INSERT INTO review_logs (id, card_id, rating, reviewed_at)
                VALUES (%s, %s, %s, %s)
                """,
                (str(uuid.uuid4()), card_id, rating, now),
            )

            updated["card_id"] = card_id
            return updated


def get_cards_due_count(user_id: str) -> int:
    """Count all of the user's cards due for review, across all decks."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM fsrs_states f
                JOIN cards c ON f.card_id = c.id
                JOIN decks d ON c.deck_id = d.id
                WHERE d.user_id = %s AND f.due_date <= CURRENT_DATE
                """,
                (user_id,),
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0


def get_streak(user_id: str) -> int:
    """Current review streak: consecutive days with >=1 review, counting
    back from today. A streak reviewed as recently as yesterday still
    counts as "current" (it isn't broken until a full day is skipped).
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT DATE(rl.reviewed_at) as day
                FROM review_logs rl
                JOIN cards c ON rl.card_id = c.id
                JOIN decks d ON c.deck_id = d.id
                WHERE d.user_id = %s
                ORDER BY day DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall()
            review_days = {row[0] for row in rows}
            return compute_streak(review_days)


def compute_streak(review_days: set, today: Optional[date] = None) -> int:
    """Pure streak calculation over a set of dates with >=1 review."""
    if not review_days:
        return 0
    if today is None:
        today = datetime.utcnow().date()

    cursor = today if today in review_days else today - timedelta(days=1)
    if cursor not in review_days:
        return 0

    streak = 0
    while cursor in review_days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _row_to_dict(row: Any, description: Any) -> Dict[str, Any]:
    """Convert a database row to a dictionary."""
    col_names = [desc[0] for desc in description]
    return dict(zip(col_names, row))
