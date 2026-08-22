"""Database service for Deck CRUD operations."""
from typing import List, Optional, Any, Dict
import uuid
from datetime import datetime

import psycopg

from app.database import get_db


def create_deck(user_id: str, name: str, description: Optional[str], tags: List[str]) -> Dict[str, Any]:
    """Create a new deck for the user."""
    deck_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO decks (id, user_id, name, description, tags, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, name, description, tags, created_at, updated_at
                """,
                (deck_id, user_id, name, description, tags, now, now)
            )
            row = cur.fetchone()
            if row:
                return _row_to_dict(row, cur.description)
    return {}


def get_deck(user_id: str, deck_id: str) -> Optional[Dict[str, Any]]:
    """Get a single deck by ID, with card count."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT d.id, d.name, d.description, d.tags, d.created_at, d.updated_at,
                       COUNT(c.id)::INTEGER as card_count
                FROM decks d
                LEFT JOIN cards c ON d.id = c.deck_id
                WHERE d.id = %s AND d.user_id = %s
                GROUP BY d.id
                """,
                (deck_id, user_id)
            )
            row = cur.fetchone()
            if row:
                return _row_to_dict(row, cur.description)
    return None


def list_decks(user_id: str) -> List[Dict[str, Any]]:
    """List all decks for the user with card counts."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT d.id, d.name, d.description, d.tags, d.created_at, d.updated_at,
                       COUNT(c.id)::INTEGER as card_count
                FROM decks d
                LEFT JOIN cards c ON d.id = c.deck_id
                WHERE d.user_id = %s
                GROUP BY d.id
                ORDER BY d.created_at DESC
                """,
                (user_id,)
            )
            rows = cur.fetchall()
            return [_row_to_dict(row, cur.description) for row in rows]


def update_deck(user_id: str, deck_id: str, name: Optional[str], 
                description: Optional[str], tags: Optional[List[str]]) -> Optional[Dict[str, Any]]:
    """Update a deck."""
    now = datetime.utcnow()
    
    with get_db() as conn:
        with conn.cursor() as cur:
            # Build dynamic UPDATE statement
            updates = []
            values = []
            if name is not None:
                updates.append("name = %s")
                values.append(name)
            if description is not None:
                updates.append("description = %s")
                values.append(description)
            if tags is not None:
                updates.append("tags = %s")
                values.append(tags)
            
            if not updates:
                # Nothing to update
                return get_deck(user_id, deck_id)
            
            updates.append("updated_at = %s")
            values.extend([now, deck_id, user_id])
            
            cur.execute(
                f"""
                UPDATE decks
                SET {', '.join(updates)}
                WHERE id = %s AND user_id = %s
                RETURNING id, name, description, tags, created_at, updated_at
                """,
                values
            )
            row = cur.fetchone()
            if row:
                return _row_to_dict(row, cur.description)
    return None


def delete_deck(user_id: str, deck_id: str) -> bool:
    """Delete a deck (cascades to cards)."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM decks WHERE id = %s AND user_id = %s",
                (deck_id, user_id)
            )
            return cur.rowcount > 0


def _row_to_dict(row: Any, description: Any) -> Dict[str, Any]:
    """Convert a database row to a dictionary."""
    col_names = [desc[0] for desc in description]
    return dict(zip(col_names, row))
