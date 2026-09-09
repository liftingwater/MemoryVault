"""Test database module for mocking Supabase operations."""
from contextlib import contextmanager
from typing import Any, Dict, List, Generator, Optional
from datetime import datetime
from unittest.mock import MagicMock, patch
import uuid

# In-memory storage for test data
_test_decks: Dict[str, Dict[str, Any]] = {}
_test_cards: Dict[str, Dict[str, Any]] = {}
_test_fsrs_states: Dict[str, Dict[str, Any]] = {}
_test_review_logs: List[Dict[str, Any]] = []


def _reset_test_data() -> None:
    """Reset all test data."""
    global _test_decks, _test_cards, _test_fsrs_states, _test_review_logs
    _test_decks.clear()
    _test_cards.clear()
    _test_fsrs_states.clear()
    _test_review_logs.clear()


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
        # Clear previous results on new query
        self._last_result = None
        self.description = None
        self._rowcount = 0
        # Normalize query for checking
        normalized = query.strip().upper()

        # Dispatch write operations first: their queries may embed a SELECT
        # subquery (e.g. DELETE ... IN (SELECT id FROM decks ...)) that would
        # otherwise be mis-matched by the SELECT branches below.
        if "INSERT INTO DECKS" in normalized:
            self._handle_insert_deck(query, params)
        elif "INSERT INTO CARDS" in normalized:
            self._handle_insert_card(query, params)
        elif "INSERT INTO FSRS_STATES" in normalized:
            self._handle_insert_fsrs_state(query, params)
        elif "INSERT INTO REVIEW_LOGS" in normalized:
            self._handle_insert_review_log(query, params)
        elif "UPDATE FSRS_STATES" in normalized:
            self._handle_update_fsrs_state(query, params)
        elif "UPDATE CARDS" in normalized:
            self._handle_update_card(query, params)
        elif "UPDATE DECKS" in normalized:
            self._handle_update_deck(query, params)
        elif "DELETE FROM CARDS" in normalized:
            self._handle_delete_card(query, params)
        elif "DELETE FROM DECKS" in normalized:
            self._handle_delete_deck(query, params)
        elif "SELECT ID FROM DECKS" in normalized:
            # Simple ownership check query
            self._handle_select_deck_id(query, params)
        elif "COUNT(*)" in normalized and "FSRS_STATES" in normalized:
            # Dashboard due-count query
            self._handle_select_due_count(query, params)
        elif "JOIN FSRS_STATES" in normalized:
            # Due cards list: FROM cards JOIN fsrs_states JOIN decks
            self._handle_select_due_cards(query, params)
        elif "FROM FSRS_STATES" in normalized:
            # Single FSRS state lookup during grading
            self._handle_select_fsrs_state(query, params)
        elif "FROM REVIEW_LOGS" in normalized:
            # Streak computation: distinct review days for the user
            self._handle_select_review_days(query, params)
        elif "SELECT" in normalized and "JOIN" in normalized:
            # Handle JOIN queries
            self._handle_select_with_join(query, params)
        elif "SELECT" in normalized and "DECKS" in normalized:
            if "COUNT(C.ID)" in normalized:
                # Check if it's a single deck query (has 2 params) or list query (has 1 param)
                if params and len(params) == 2:
                    self._handle_select_deck_with_count(query, params)
                else:
                    self._handle_select_decks(query, params)
            else:
                self._handle_select_decks(query, params)
        elif "SELECT" in normalized and "CARDS" in normalized:
            self._handle_select_cards(query, params)
    
    def _handle_select_deck_id(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle SELECT id FROM decks WHERE id = ? AND user_id = ? query."""
        if params and len(params) == 2:
            deck_id, user_id = params
            if deck_id in _test_decks and _test_decks[deck_id]["user_id"] == user_id:
                self._last_result = [(deck_id,)]
                self.description = [("id",)]
                self._rowcount = 1
            else:
                self._last_result = []
                self.description = [("id",)]
                self._rowcount = 0

    def _handle_select_with_join(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle SELECT queries with JOINs."""
        if not params:
            self._last_result = []
            return

        if "JOIN decks d ON c.deck_id = d.id" in query:
            # This is a cards JOIN decks query
            card_id, user_id = params

            # Check if card exists and belongs to user
            if card_id in _test_cards:
                card = _test_cards[card_id]
                deck_id = card["deck_id"]
                if deck_id in _test_decks and _test_decks[deck_id]["user_id"] == user_id:
                    self._last_result = [(card_id,)]
                    self.description = [("id",)]
                    self._rowcount = 1
                else:
                    self._last_result = []
                    self._rowcount = 0
            else:
                self._last_result = []
                self._rowcount = 0
        else:
            self._last_result = []
            self._rowcount = 0

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
            # Verify deck exists
            if deck_id not in _test_decks:
                self._rowcount = 0
                return

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
            self.description = [
                ("id",), ("deck_id",), ("card_type",), ("front_md",), ("back_md",),
                ("cloze_text_md",), ("cloze_answer",), ("created_at",), ("updated_at",)
            ]
            self._rowcount = 1

    # ── FSRS / review ────────────────────────────────────────────────────

    _FSRS_STATE_COLUMNS = [
        ("card_id",), ("stability",), ("difficulty",), ("due_date",),
        ("last_review",), ("reps",), ("lapses",), ("state",)
    ]

    def _handle_insert_fsrs_state(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle INSERT INTO fsrs_states query."""
        if params:
            card_id, stability, difficulty, due_date, last_review, reps, lapses, state = params
            _test_fsrs_states[card_id] = {
                "card_id": card_id,
                "stability": stability,
                "difficulty": difficulty,
                "due_date": due_date,
                "last_review": last_review,
                "reps": reps,
                "lapses": lapses,
                "state": state,
            }
            self._rowcount = 1

    def _handle_update_fsrs_state(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle UPDATE fsrs_states query."""
        if params and len(params) == 8:
            stability, difficulty, due_date, last_review, reps, lapses, state, card_id = params
            if card_id in _test_fsrs_states:
                _test_fsrs_states[card_id].update({
                    "stability": stability,
                    "difficulty": difficulty,
                    "due_date": due_date,
                    "last_review": last_review,
                    "reps": reps,
                    "lapses": lapses,
                    "state": state,
                })
                self._rowcount = 1
            else:
                self._rowcount = 0

    def _handle_insert_review_log(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle INSERT INTO review_logs query."""
        if params:
            log_id, card_id, rating, reviewed_at = params
            _test_review_logs.append({
                "id": log_id,
                "card_id": card_id,
                "rating": rating,
                "reviewed_at": reviewed_at,
            })
            self._rowcount = 1

    def _handle_select_due_count(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle SELECT COUNT(*) FROM fsrs_states ... query (dashboard)."""
        if not params:
            return
        user_id = params[0]
        today = datetime.utcnow().date()
        count = 0
        for card_id, fsrs in _test_fsrs_states.items():
            card = _test_cards.get(card_id)
            deck = _test_decks.get(card["deck_id"]) if card else None
            if deck and deck["user_id"] == user_id and fsrs["due_date"] <= today:
                count += 1
        self._last_result = [(count,)]
        self.description = [("count",)]
        self._rowcount = 1

    def _handle_select_due_cards(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle the due-cards query: cards JOIN fsrs_states JOIN decks."""
        if not params:
            self._last_result = []
            return
        user_id = params[0]
        deck_filter = params[1] if len(params) > 1 else None
        today = datetime.utcnow().date()

        due = []
        for card_id, fsrs in _test_fsrs_states.items():
            card = _test_cards.get(card_id)
            if not card:
                continue
            deck = _test_decks.get(card["deck_id"])
            if not deck or deck["user_id"] != user_id:
                continue
            if deck_filter and card["deck_id"] != deck_filter:
                continue
            if fsrs["due_date"] <= today:
                due.append((fsrs["due_date"], card["created_at"], card))

        due.sort(key=lambda t: (t[0], t[1]))
        self._last_result = [self._card_to_row(c) for _, _, c in due]
        self.description = [
            ("id",), ("deck_id",), ("card_type",), ("front_md",), ("back_md",),
            ("cloze_text_md",), ("cloze_answer",), ("created_at",), ("updated_at",)
        ]

    def _handle_select_fsrs_state(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle the single FSRS-state-with-ownership-check lookup used during grading."""
        self.description = self._FSRS_STATE_COLUMNS
        if not params or len(params) < 2:
            self._last_result = []
            return
        card_id, user_id = params
        fsrs = _test_fsrs_states.get(card_id)
        card = _test_cards.get(card_id)
        deck = _test_decks.get(card["deck_id"]) if card else None
        if not fsrs or not deck or deck["user_id"] != user_id:
            self._last_result = []
            return
        self._last_result = [(
            fsrs["card_id"], fsrs["stability"], fsrs["difficulty"], fsrs["due_date"],
            fsrs["last_review"], fsrs["reps"], fsrs["lapses"], fsrs["state"],
        )]

    def _handle_select_review_days(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle the distinct-review-days query used for streak computation."""
        self.description = [("day",)]
        if not params:
            self._last_result = []
            return
        user_id = params[0]
        days = set()
        for log in _test_review_logs:
            card = _test_cards.get(log["card_id"])
            deck = _test_decks.get(card["deck_id"]) if card else None
            if not deck or deck["user_id"] != user_id:
                continue
            reviewed_at = log["reviewed_at"]
            day = reviewed_at.date() if isinstance(reviewed_at, datetime) else reviewed_at
            days.add(day)
        self._last_result = [(d,) for d in sorted(days, reverse=True)]

    def _handle_select_cards(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle SELECT cards query."""
        if not params:
            self._last_result = []
            return

        deck_id = params[0]

        # Verify deck exists
        if deck_id not in _test_decks:
            self._last_result = []
            self.description = [
                ("id",), ("deck_id",), ("card_type",), ("front_md",), ("back_md",),
                ("cloze_text_md",), ("cloze_answer",), ("created_at",), ("updated_at",)
            ]
            return

        # Filter cards by deck
        cards = [c for c in _test_cards.values() if c["deck_id"] == deck_id]

        # Apply search filter if present (for ILIKE queries, we get multiple search patterns)
        # If there are more than 1 param, it's a search query
        if len(params) > 1:
            # Search patterns are params[1], params[2], params[3] (front_md, back_md, cloze_text_md)
            # Extract the search text (remove % wildcards)
            search_text = params[1].strip('%').lower() if params[1] else ""
            if search_text:
                cards = [c for c in cards if (
                    search_text in c["front_md"].lower() or
                    (c["back_md"] and search_text in c["back_md"].lower()) or
                    (c["cloze_text_md"] and search_text in c["cloze_text_md"].lower())
                )]

        # Sort by created_at DESC
        cards = sorted(cards, key=lambda x: x["created_at"], reverse=True)
        self._last_result = [self._card_to_row(c) for c in cards]
        self.description = [
            ("id",), ("deck_id",), ("card_type",), ("front_md",), ("back_md",),
            ("cloze_text_md",), ("cloze_answer",), ("created_at",), ("updated_at",)
        ]

    def _handle_update_card(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle UPDATE cards query."""
        if not params or len(params) < 2:
            self._rowcount = 0
            return

        # Last param is always card_id
        card_id = params[-1]

        if card_id not in _test_cards:
            self._rowcount = 0
            return

        # Map updates based on query
        update_values = params[:-1]
        idx = 0

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
        if "updated_at =" in query and idx < len(update_values):
            _test_cards[card_id]["updated_at"] = update_values[idx]
            idx += 1

        card = _test_cards[card_id]
        self._last_result = [self._card_to_row(card)]
        self.description = [
            ("id",), ("deck_id",), ("card_type",), ("front_md",), ("back_md",),
            ("cloze_text_md",), ("cloze_answer",), ("created_at",), ("updated_at",)
        ]
        self._rowcount = 1

    def _handle_delete_card(self, query: str, params: Optional[List[Any]]) -> None:
        """Handle DELETE FROM cards query."""
        if not params or len(params) < 2:
            self._rowcount = 0
            return

        card_id = params[0]
        user_id = params[1]

        # Check if card exists and belongs to user's deck
        if card_id in _test_cards:
            card = _test_cards[card_id]
            deck_id = card["deck_id"]
            # Verify deck belongs to user
            if deck_id in _test_decks and _test_decks[deck_id]["user_id"] == user_id:
                del _test_cards[card_id]
                self._rowcount = 1
            else:
                self._rowcount = 0
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
        # psycopg returns the uuid column as a uuid.UUID, so mirror that here.
        return (uuid.UUID(deck["id"]), deck["name"], deck["description"], deck["tags"],
                deck["created_at"], deck["updated_at"])

    @staticmethod
    def _deck_to_row_with_count(deck: Dict[str, Any]) -> tuple:
        """Convert deck dict to row tuple with card count."""
        # psycopg returns the uuid column as a uuid.UUID, so mirror that here.
        return (uuid.UUID(deck["id"]), deck["name"], deck["description"], deck["tags"],
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
