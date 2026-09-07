"""Database service for Card CRUD operations."""
from typing import List, Optional, Any, Dict
import uuid
from datetime import datetime

from app.database import get_db
from app.services.fsrs_service import initial_state


def create_card(
    user_id: str,
    deck_id: str,
    card_type: str,
    front_md: str,
    back_md: Optional[str],
    cloze_text_md: Optional[str],
    cloze_answer: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Create a new card in a deck."""
    card_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    with get_db() as conn:
        with conn.cursor() as cur:
            # Verify deck ownership
            cur.execute(
                "SELECT id FROM decks WHERE id = %s AND user_id = %s",
                (deck_id, user_id)
            )
            if not cur.fetchone():
                return None
            
            # Create card
            cur.execute(
                """
                INSERT INTO cards (id, deck_id, card_type, front_md, back_md, cloze_text_md, cloze_answer, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, deck_id, card_type, front_md, back_md, cloze_text_md, cloze_answer, created_at, updated_at
                """,
                (card_id, deck_id, card_type, front_md, back_md, cloze_text_md, cloze_answer, now, now)
            )
            row = cur.fetchone()
            if not row:
                return None
            card = _row_to_dict(row, cur.description)

            # Every new card starts out due for review immediately (state=new).
            fsrs_row = initial_state(now)
            cur.execute(
                """
                INSERT INTO fsrs_states (card_id, stability, difficulty, due_date, last_review, reps, lapses, state)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    card_id, fsrs_row["stability"], fsrs_row["difficulty"],
                    fsrs_row["due_date"], fsrs_row["last_review"],
                    fsrs_row["reps"], fsrs_row["lapses"], fsrs_row["state"],
                )
            )

            return card
    return None


def list_cards(
    user_id: str,
    deck_id: str,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List cards in a deck with optional search."""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Verify deck ownership
            cur.execute(
                "SELECT id FROM decks WHERE id = %s AND user_id = %s",
                (deck_id, user_id)
            )
            if not cur.fetchone():
                return []
            
            # Build search query
            query = "SELECT id, deck_id, card_type, front_md, back_md, cloze_text_md, cloze_answer, created_at, updated_at FROM cards WHERE deck_id = %s"
            params = [deck_id]
            
            if search:
                query += " AND (front_md ILIKE %s OR back_md ILIKE %s OR cloze_text_md ILIKE %s)"
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            query += " ORDER BY created_at DESC"
            cur.execute(query, params)
            rows = cur.fetchall()
            return [_row_to_dict(row, cur.description) for row in rows]


def get_card(user_id: str, card_id: str) -> Optional[Dict[str, Any]]:
    """Get a single card by ID (with ownership check)."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id, c.deck_id, c.card_type, c.front_md, c.back_md, c.cloze_text_md, c.cloze_answer, c.created_at, c.updated_at
                FROM cards c
                JOIN decks d ON c.deck_id = d.id
                WHERE c.id = %s AND d.user_id = %s
                """,
                (card_id, user_id)
            )
            row = cur.fetchone()
            if row:
                return _row_to_dict(row, cur.description)
    return None


def update_card(
    user_id: str,
    card_id: str,
    front_md: Optional[str],
    back_md: Optional[str],
    cloze_text_md: Optional[str],
    cloze_answer: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Update a card."""
    now = datetime.utcnow()
    
    with get_db() as conn:
        with conn.cursor() as cur:
            # Verify ownership
            cur.execute(
                """
                SELECT c.id FROM cards c
                JOIN decks d ON c.deck_id = d.id
                WHERE c.id = %s AND d.user_id = %s
                """,
                (card_id, user_id)
            )
            if not cur.fetchone():
                return None
            
            # Build update
            updates = []
            values = []
            if front_md is not None:
                updates.append("front_md = %s")
                values.append(front_md)
            if back_md is not None:
                updates.append("back_md = %s")
                values.append(back_md)
            if cloze_text_md is not None:
                updates.append("cloze_text_md = %s")
                values.append(cloze_text_md)
            if cloze_answer is not None:
                updates.append("cloze_answer = %s")
                values.append(cloze_answer)
            
            if not updates:
                return get_card(user_id, card_id)
            
            updates.append("updated_at = %s")
            values.extend([now, card_id])
            
            cur.execute(
                f"""
                UPDATE cards
                SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, deck_id, card_type, front_md, back_md, cloze_text_md, cloze_answer, created_at, updated_at
                """,
                values
            )
            row = cur.fetchone()
            if row:
                return _row_to_dict(row, cur.description)
    return None


def delete_card(user_id: str, card_id: str) -> bool:
    """Delete a card."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM cards
                WHERE id = %s AND deck_id IN (SELECT id FROM decks WHERE user_id = %s)
                """,
                (card_id, user_id)
            )
            return cur.rowcount > 0


def _row_to_dict(row: Any, description: Any) -> Dict[str, Any]:
    """Convert a database row to a dictionary."""
    col_names = [desc[0] for desc in description]
    return dict(zip(col_names, row))
