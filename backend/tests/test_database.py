"""Test database module for mocking Supabase operations."""
from contextlib import contextmanager
from typing import Any, Dict, List, Generator, Optional
from datetime import datetime
from unittest.mock import MagicMock, patch
import uuid

# In-memory storage for test data
_test_decks: Dict[str, Dict[str, Any]] = {}


def _reset_test_data() -> None:
    """Reset all test data."""
    global _test_decks
    _test_decks.clear()


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
        elif "SELECT" in query and "decks" in query:
            if "COUNT(c.id)" in query:
                # Check if it's a single deck query (has 2 params) or list query (has 1 param)
                if params and len(params) == 2:
                    self._handle_select_deck_with_count(query, params)
                else:
                    self._handle_select_decks(query, params)
            else:
                self._handle_select_decks(query, params)
        elif "UPDATE decks" in query:
            self._handle_update_deck(query, params)
        elif "DELETE FROM decks" in query:
            self._handle_delete_deck(query, params)
    
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
