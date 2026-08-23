"""Database service for Card CRUD operations."""
from typing import List, Optional, Any, Dict
import uuid
from datetime import datetime

import psycopg

from app.database import get_db


def create_card(deck_id: str, card_type: str, front_md: Optional[str],
                back_md: Optional[str], cloze_text_md: Optional[str],
                cloze_answer: Optional[str]) -> Dict[str, Any]:
    """Create a new card in a deck."""
    card_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cards (id, deck_id, card_type, front_md, back_md, 
                                   cloze_text_md, cloze_answer, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, deck_id, card_type, front_md, back_md, cloze_text_md, 
                          cloze_answer, created_at, updated_at
                """,
                (card_id, deck_id, card_type, front_md, back_md, 
                 cloze_text_md, cloze_answer, now, now)
            )
            row = cur.fetchone()
            if row:
                return _row_to_dict(row, cur.description)
    return {}


def get_card(card_id: str) -> Optional[Dict[str, Any]]:
    """Get a single card by ID."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, deck_id, card_type, front_md, back_md, cloze_text_md,
                       cloze_answer, created_at, updated_at
                FROM cards WHERE id = %s
                """,
                (card_id,)
            )
            row = cur.fetchone()
            if row:
                return _row_to_dict(row, cur.description)
    return None


def list_cards(deck_id: str, search: Optional[str] = None) -> List[Dict[str, Any]]:
    """List cards in a deck with optional search."""
    with get_db() as conn:
        with conn.cursor() as cur:
            if search:
                cur.execute(
                    """
                    SELECT id, deck_id, card_type, front_md, back_md, cloze_text_md,
                           cloze_answer, created_at, updated_at
                    FROM cards 
                    WHERE deck_id = %s AND (front_md ILIKE %s OR cloze_text_md ILIKE %s)
                    ORDER BY created_at DESC
                    """,
                    (deck_id, f"%{search}%", f"%{search}%")
                )
            else:
                cur.execute(
                    """
                    SELECT id, deck_id, card_type, front_md, back_md, cloze_text_md,
                           cloze_answer, created_at, updated_at
                    FROM cards WHERE deck_id = %s
                    ORDER BY created_at DESC
                    """,
                    (deck_id,)
                )
            rows = cur.fetchall()
            return [_row_to_dict(row, cur.description) for row in rows]


def update_card(card_id: str, card_type: Optional[str], front_md: Optional[str],
                back_md: Optional[str], cloze_text_md: Optional[str],
                cloze_answer: Optional[str]) -> Optional[Dict[str, Any]]:
    """Update a card."""
    now = datetime.utcnow()
    
    with get_db() as conn:
        with conn.cursor() as cur:
            updates = []
            values = []
            if card_type is not None:
                updates.append("card_type = %s")
                values.append(card_type)
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
                return get_card(card_id)
            
            updates.append("updated_at = %s")
            values.extend([now, card_id])
            
            cur.execute(
                f"""
                UPDATE cards SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, deck_id, card_type, front_md, back_md, cloze_text_md,
                          cloze_answer, created_at, updated_at
                """,
                values
            )
            row = cur.fetchone()
            if row:
                return _row_to_dict(row, cur.description)
    return None


def delete_card(card_id: str) -> bool:
    """Delete a card."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM cards WHERE id = %s", (card_id,))
            return cur.rowcount > 0


def _row_to_dict(row: Any, description: Any) -> Dict[str, Any]:
    """Convert a database row to a dictionary."""
    col_names = [desc[0] for desc in description]
    return dict(zip(col_names, row))
