"""Test database module for mocking Supabase operations."""
from contextlib import contextmanager
from typing import Any, Dict, List, Generator, Optional
from datetime import datetime
from unittest.mock import MagicMock, patch
import uuid

# In-memory storage for test data
_test_decks: Dict[str, Dict[str, Any]] = {}
_test_cards: Dict[str, Dict[str, Any]] = {}


def _reset_test_data() -> None:
    """Reset all test data."""
    global _test_decks, _test_cards
    _test_decks.clear()
    _test_cards.clear()


class MockCursor:
    """Mock psycopg cursor for testing."""

    def __init__(self) -> None:
        self.description: Optional[List[tuple]] = None
        self._rowcount = 0
        self._last_result: Optional[List[tuple]] = None

    @property
    def rowcount(self) -> int:
        return self._rowcount

    def __enter__(self) -> "MockCursor":
        return self

    def __exit__(self, *args: Any) -> None:
        pass
    
    def execute(self, query: str, params: Optional[List[Any]] = None) -> None:
        """Execute a mocked SQL query."""
        if "INSERT INTO decks" in query:
            self._handle_insert_deck(query, params)
        elif "INSERT INTO cards" in query:
            self._handle_insert_card(query, params)
        elif "SELECT" in query and "decks" in query:
            if "COUNT(c.id)" in query:
                # Check if it's a single deck query (has 2 params) or list query (has 1 param)
                if params and len(params) == 2:
                    self._handle_select_deck_with_count(query, params)
                else:
                    self._handle_select_decks(query, params)
            else:
                self._handle_select_decks(query, params)
        elif "SELECT" in query and "cards" in query:
            self._handle_select_cards(query, params)
        elif "UPDATE decks" in query:
            self._handle_update_deck(query, params)
        elif "UPDATE cards" in query:
            self._handle_update_card(query, params)
        elif "DELETE FROM decks" in query:
            self._handle_delete_deck(query, params)
        elif "DELETE FROM cards" in query:
            self._handle_delete_card(query, params)
    
    def _handle_insert_deck(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle INSERT INTO decks query."""
        if params:
            deck_id, user_id, name, description, tags, created_at, updated_at = params
            deck = {
                "id": deck_id,
                "user_id": user_id,
                "name": name,
                "description": description,
                "tags": tags or [],
                "created_at": created_at,
                "updated_at": updated_at,
                "card_count": 0,
            }
            _test_decks[deck_id] = deck
            self._last_result = [self._deck_to_row(deck)]
            self.description = [("id",), ("name",), ("description",), ("tags",), ("created_at",), ("updated_at",)]
            self._rowcount = 1
    
    def _handle_select_deck_with_count(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle SELECT with COUNT(c.id)."""
        if params:
            deck_id, user_id = params
            if deck_id in _test_decks and _test_decks[deck_id]["user_id"] == user_id:
                deck = _test_decks[deck_id].copy()
                self._last_result = [self._deck_to_row_with_count(deck)]
                self.description = [
                    ("id",), ("name",), ("description",), ("tags",),
                    ("created_at",), ("updated_at",), ("card_count",)
                ]
            else:
                self._last_result = []
                self.description = []
    
    def _handle_select_decks(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle SELECT decks query."""
        if params:
            user_id = params[0]
            decks = [d for d in _test_decks.values() if d["user_id"] == user_id]
            decks = sorted(decks, key=lambda x: x["created_at"], reverse=True)
            self._last_result = [self._deck_to_row_with_count(d) for d in decks]
            if self._last_result:
                self.description = [
                    ("id",), ("name",), ("description",), ("tags",),
                    ("created_at",), ("updated_at",), ("card_count",)
                ]
            else:
                # Empty result but still set description
                self.description = [
                    ("id",), ("name",), ("description",), ("tags",),
                    ("created_at",), ("updated_at",), ("card_count",)
                ]
    
    def _handle_update_deck(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle UPDATE decks query."""
        if params and len(params) >= 3:
            # Last two params are always deck_id, user_id
            deck_id = params[-2]
            user_id = params[-1]

            if deck_id in _test_decks and _test_decks[deck_id]["user_id"] == user_id:
                # All params except the last 2 (deck_id, user_id) are the update values
                # The order matches the SET clause in the query
                update_values = params[:-2]

                # Map updates based on which values are in params
                # This handles partial updates where name, description, tags may be present
                idx = 0
                if "name =" in query and idx < len(update_values):
                    _test_decks[deck_id]["name"] = update_values[idx]
                    idx += 1
                if "description =" in query and idx < len(update_values):
                    _test_decks[deck_id]["description"] = update_values[idx]
                    idx += 1
                if "tags =" in query and idx < len(update_values):
                    _test_decks[deck_id]["tags"] = update_values[idx]
                    idx += 1

                _test_decks[deck_id]["updated_at"] = datetime.utcnow()
                deck = _test_decks[deck_id]
                self._last_result = [self._deck_to_row(deck)]
                self.description = [("id",), ("name",), ("description",), ("tags",), ("created_at",), ("updated_at",)]
                self._rowcount = 1
            else:
                self._rowcount = 0
                self._last_result = []
    
    def _handle_delete_deck(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle DELETE FROM decks query."""
        if params:
            deck_id, user_id = params
            if deck_id in _test_decks and _test_decks[deck_id]["user_id"] == user_id:
                del _test_decks[deck_id]
                self._rowcount = 1
            else:
                self._rowcount = 0

    def _handle_insert_card(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle INSERT INTO cards query."""
        if params:
            card_id, deck_id, card_type, front_md, back_md, cloze_text_md, cloze_answer, created_at, updated_at = params
            card = {
                "id": card_id,
                "deck_id": deck_id,
                "card_type": card_type,
                "front_md": front_md,
                "back_md": back_md,
                "cloze_text_md": cloze_text_md,
                "cloze_answer": cloze_answer,
                "created_at": created_at,
                "updated_at": updated_at,
            }
            _test_cards[card_id] = card
            self._last_result = [self._card_to_row(card)]
            self.description = [("id",), ("deck_id",), ("card_type",), ("front_md",), ("back_md",),
                               ("cloze_text_md",), ("cloze_answer",), ("created_at",), ("updated_at",)]
            self._rowcount = 1

    def _handle_select_cards(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle SELECT cards query."""
        if not params:
            return

        if "WHERE id =" in query:
            # Single card by ID
            card_id = params[0]
            if card_id in _test_cards:
                card = _test_cards[card_id]
                self._last_result = [self._card_to_row(card)]
                self.description = [("id",), ("deck_id",), ("card_type",), ("front_md",), ("back_md",),
                                   ("cloze_text_md",), ("cloze_answer",), ("created_at",), ("updated_at",)]
            else:
                self._last_result = []
                self.description = []
        elif "WHERE deck_id = %s" in query:
            # Cards in a deck with optional search
            deck_id = params[0]
            cards = [c for c in _test_cards.values() if c["deck_id"] == deck_id]

            # Apply search filter if present (ILIKE with % patterns)
            if len(params) > 1:
                # Search params come as "%search%" format from the service
                search = params[1]
                # Remove the % wildcards to get the actual search term
                search_term = search.strip("%")
                cards = [c for c in cards if (
                    (c.get("front_md") and search_term.lower() in c["front_md"].lower()) or
                    (c.get("cloze_text_md") and search_term.lower() in c["cloze_text_md"].lower())
                )]

            cards = sorted(cards, key=lambda x: x["created_at"], reverse=True)
            self._last_result = [self._card_to_row(c) for c in cards]
            if self._last_result:
                self.description = [("id",), ("deck_id",), ("card_type",), ("front_md",), ("back_md",),
                                   ("cloze_text_md",), ("cloze_answer",), ("created_at",), ("updated_at",)]
            else:
                self.description = [("id",), ("deck_id",), ("card_type",), ("front_md",), ("back_md",),
                                   ("cloze_text_md",), ("cloze_answer",), ("created_at",), ("updated_at",)]

    def _handle_update_card(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle UPDATE cards query."""
        if not params:
            return

        card_id = params[-1]
        if card_id not in _test_cards:
            self._rowcount = 0
            self._last_result = []
            return

        update_values = params[:-1]
        idx = 0

        if "card_type =" in query and idx < len(update_values):
            _test_cards[card_id]["card_type"] = update_values[idx]
            idx += 1
        if "front_md =" in query and idx < len(update_values):
            _test_cards[card_id]["front_md"] = update_values[idx]
            idx += 1
        if "back_md =" in query and idx < len(update_values):
            _test_cards[card_id]["back_md"] = update_values[idx]
            idx += 1
        if "cloze_text_md =" in query and idx < len(update_values):
            _test_cards[card_id]["cloze_text_md"] = update_values[idx]
            idx += 1
        if "cloze_answer =" in query and idx < len(update_values):
            _test_cards[card_id]["cloze_answer"] = update_values[idx]
            idx += 1

        _test_cards[card_id]["updated_at"] = datetime.utcnow()
        card = _test_cards[card_id]
        self._last_result = [self._card_to_row(card)]
        self.description = [("id",), ("deck_id",), ("card_type",), ("front_md",), ("back_md",),
                           ("cloze_text_md",), ("cloze_answer",), ("created_at",), ("updated_at",)]
        self._rowcount = 1

    def _handle_delete_card(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle DELETE FROM cards query."""
        if params:
            card_id = params[0]
            if card_id in _test_cards:
                del _test_cards[card_id]
                self._rowcount = 1
            else:
                self._rowcount = 0

    def fetchone(self) -> Optional[tuple]:
        """Fetch one result."""
        return self._last_result[0] if self._last_result else None
    
    def fetchall(self) -> List[tuple]:
        """Fetch all results."""
        return self._last_result or []
    
    @staticmethod
    def _deck_to_row(deck: Dict[str, Any]) -> tuple:
        """Convert deck dict to row tuple."""
        return (deck["id"], deck["name"], deck["description"], deck["tags"],
                deck["created_at"], deck["updated_at"])
    
    @staticmethod
    def _deck_to_row_with_count(deck: Dict[str, Any]) -> tuple:
        """Convert deck dict to row tuple with card count."""
        return (deck["id"], deck["name"], deck["description"], deck["tags"],
                deck["created_at"], deck["updated_at"], deck.get("card_count", 0))

    @staticmethod
    def _card_to_row(card: Dict[str, Any]) -> tuple:
        """Convert card dict to row tuple."""
        return (card["id"], card["deck_id"], card["card_type"], card["front_md"],
                card["back_md"], card["cloze_text_md"], card["cloze_answer"],
                card["created_at"], card["updated_at"])


class MockConnection:
    """Mock psycopg connection for testing."""
    
    def __init__(self) -> None:
        self._cursor = MockCursor()
    
    def cursor(self) -> MockCursor:
        """Get a mock cursor."""
        return self._cursor
    
    def commit(self) -> None:
        """Mock commit."""
        pass
    
    def rollback(self) -> None:
        """Mock rollback."""
        pass
    
    def close(self) -> None:
        """Mock close."""
        pass
    
    def __enter__(self) -> "MockConnection":
        return self
    
    def __exit__(self, *args: Any) -> None:
        pass


@contextmanager
def mock_get_db() -> Generator[MockConnection, None, None]:
    """Context manager for mocked database connection."""
    conn = MockConnection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
