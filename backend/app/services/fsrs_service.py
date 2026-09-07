"""Wraps py-fsrs so the rest of the app only deals with our own FSRSState
row shape (the dict stored in/read from the `fsrs_states` table), never the
library's `Card` object directly.

MVP uses binary grading only (got_it/need_review), so the scheduler is
configured with no learning/relearning steps: every review transitions a
card straight into the `review` state, and there is no multi-step
Learning/Relearning drilling. A card is `new` until its first review.
"""
from datetime import datetime, time, timezone
from typing import Any, Dict

from fsrs import Card as FSRSCard, Rating as FSRSRating, Scheduler
from fsrs import State as FSRSState

_scheduler = Scheduler(learning_steps=(), relearning_steps=())

_STATE_TO_STR = {
    FSRSState.Learning: "learning",
    FSRSState.Review: "review",
    FSRSState.Relearning: "relearning",
}

_RATING_TO_FSRS = {
    "got_it": FSRSRating.Good,
    "need_review": FSRSRating.Again,
}


def initial_state(now: datetime) -> Dict[str, Any]:
    """The FSRSState row for a freshly created card: new, due immediately."""
    return {
        "stability": 0.0,
        "difficulty": 0.0,
        "due_date": now.date(),
        "last_review": None,
        "reps": 0,
        "lapses": 0,
        "state": "new",
    }


def apply_review(
    fsrs_row: Dict[str, Any], rating: str, review_datetime: datetime
) -> Dict[str, Any]:
    """Apply a binary grade to a stored FSRS state and return the updated row.

    `fsrs_row` is a dict shaped like an `fsrs_states` table row (stability,
    difficulty, due_date, last_review, reps, lapses, state).
    """
    if review_datetime.tzinfo is None:
        review_datetime = review_datetime.replace(tzinfo=timezone.utc)

    is_new = fsrs_row["state"] == "new"
    if is_new:
        card = FSRSCard(card_id=0)
    else:
        last_review = fsrs_row["last_review"]
        card = FSRSCard(
            card_id=0,
            state=FSRSState.Review,
            step=None,
            stability=fsrs_row["stability"],
            difficulty=fsrs_row["difficulty"],
            due=datetime.combine(fsrs_row["due_date"], time.min, tzinfo=timezone.utc),
            last_review=(
                datetime.combine(last_review, time.min, tzinfo=timezone.utc)
                if last_review is not None
                else None
            ),
        )

    updated_card, _log = _scheduler.review_card(
        card, _RATING_TO_FSRS[rating], review_datetime=review_datetime
    )

    # A "lapse" is forgetting a card that had already graduated past `new`.
    is_lapse = (not is_new) and rating == "need_review"

    assert updated_card.last_review is not None
    return {
        "stability": updated_card.stability,
        "difficulty": updated_card.difficulty,
        "due_date": updated_card.due.date(),
        "last_review": updated_card.last_review.date(),
        "reps": fsrs_row["reps"] + 1,
        "lapses": fsrs_row["lapses"] + (1 if is_lapse else 0),
        "state": _STATE_TO_STR[updated_card.state],
    }
