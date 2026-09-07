"""Test the FSRS review flow: due retrieval, grading, and streaks."""
import uuid
from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient

from app.services.review_service import compute_streak
from tests.conftest import create_test_jwt


def _create_deck_and_card(client: TestClient, token: str) -> tuple[str, str]:
    deck_response = client.post(
        "/api/decks",
        json={"name": "Test Deck"},
        headers={"Authorization": f"Bearer {token}"},
    )
    deck_id = deck_response.json()["id"]
    card_response = client.post(
        f"/api/decks/{deck_id}/cards",
        json={"card_type": "front_back", "front_md": "Q", "back_md": "A"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return deck_id, card_response.json()["id"]


# ── New cards start due immediately ─────────────────────────────────────────


def test_new_card_appears_in_due_queue(client: TestClient) -> None:
    """A freshly created card gets an FSRSState (new, due now) and is due."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    _deck_id, card_id = _create_deck_and_card(client, token)

    response = client.get("/api/review/due", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["cards"][0]["id"] == card_id


def test_due_cards_requires_auth(client: TestClient) -> None:
    response = client.get("/api/review/due")
    assert response.status_code == 403


def test_due_cards_filters_by_deck(client: TestClient) -> None:
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    deck1_id, _card1 = _create_deck_and_card(client, token)
    deck2_id, card2 = _create_deck_and_card(client, token)

    response = client.get(
        f"/api/review/due?deck_id={deck2_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["cards"][0]["id"] == card2


def test_due_cards_excludes_other_users_cards(client: TestClient) -> None:
    token1 = create_test_jwt(str(uuid.uuid4()))
    token2 = create_test_jwt(str(uuid.uuid4()))
    _create_deck_and_card(client, token1)

    response = client.get("/api/review/due", headers={"Authorization": f"Bearer {token2}"})

    assert response.status_code == 200
    assert response.json()["total"] == 0


# ── Grading ──────────────────────────────────────────────────────────────────


def test_grade_card_requires_auth(client: TestClient) -> None:
    response = client.post(f"/api/review/{uuid.uuid4()}", json={"rating": "got_it"})
    assert response.status_code == 403


def test_grade_card_not_found(client: TestClient) -> None:
    token = create_test_jwt(str(uuid.uuid4()))
    response = client.post(
        f"/api/review/{uuid.uuid4()}",
        json={"rating": "got_it"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_grade_card_wrong_owner(client: TestClient) -> None:
    token1 = create_test_jwt(str(uuid.uuid4()))
    token2 = create_test_jwt(str(uuid.uuid4()))
    _deck_id, card_id = _create_deck_and_card(client, token1)

    response = client.post(
        f"/api/review/{card_id}",
        json={"rating": "got_it"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 404


def test_grade_card_rejects_invalid_rating(client: TestClient) -> None:
    token = create_test_jwt(str(uuid.uuid4()))
    _deck_id, card_id = _create_deck_and_card(client, token)

    response = client.post(
        f"/api/review/{card_id}",
        json={"rating": "sort_of"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_grade_card_got_it_updates_fsrs_state_and_logs_review(client: TestClient) -> None:
    token = create_test_jwt(str(uuid.uuid4()))
    _deck_id, card_id = _create_deck_and_card(client, token)

    response = client.post(
        f"/api/review/{card_id}",
        json={"rating": "got_it"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["card_id"] == card_id
    assert data["state"] == "review"
    assert data["reps"] == 1
    assert data["lapses"] == 0
    today = datetime.utcnow().date().isoformat()
    assert data["last_review"] == today
    # Binary "Good" schedules the card into the future, out of today's queue.
    assert data["due_date"] > today


def test_grade_card_need_review_keeps_card_learnable(client: TestClient) -> None:
    token = create_test_jwt(str(uuid.uuid4()))
    _deck_id, card_id = _create_deck_and_card(client, token)

    response = client.post(
        f"/api/review/{card_id}",
        json={"rating": "need_review"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reps"] == 1
    # First-ever review isn't a lapse (the card was never learned yet).
    assert data["lapses"] == 0


def test_grade_card_second_lapse_increments_lapses(client: TestClient) -> None:
    token = create_test_jwt(str(uuid.uuid4()))
    _deck_id, card_id = _create_deck_and_card(client, token)

    client.post(
        f"/api/review/{card_id}",
        json={"rating": "got_it"},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.post(
        f"/api/review/{card_id}",
        json={"rating": "need_review"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["lapses"] == 1


def test_mid_session_quit_leaves_ungraded_cards_in_queue(client: TestClient) -> None:
    """Grading one card removes it from the due queue; the other stays."""
    token = create_test_jwt(str(uuid.uuid4()))
    _deck_id, card1 = _create_deck_and_card(client, token)
    _deck_id2, card2 = _create_deck_and_card(client, token)

    client.post(
        f"/api/review/{card1}",
        json={"rating": "got_it"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get("/api/review/due", headers={"Authorization": f"Bearer {token}"})
    data = response.json()
    assert data["total"] == 1
    assert data["cards"][0]["id"] == card2


# ── Dashboard ────────────────────────────────────────────────────────────────


def test_dashboard_reports_cards_due_and_streak(client: TestClient) -> None:
    token = create_test_jwt(str(uuid.uuid4()))
    _create_deck_and_card(client, token)
    _deck_id, card2 = _create_deck_and_card(client, token)
    client.post(
        f"/api/review/{card2}",
        json={"rating": "got_it"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["cards_due"] == 1
    assert data["streak"] == 1


# ── Streak computation (pure function) ──────────────────────────────────────


def test_compute_streak_empty_is_zero() -> None:
    assert compute_streak(set()) == 0


def test_compute_streak_counts_consecutive_days_ending_today() -> None:
    today = date(2026, 9, 7)
    days = {today, today - timedelta(days=1), today - timedelta(days=2)}
    assert compute_streak(days, today=today) == 3


def test_compute_streak_still_current_if_last_review_was_yesterday() -> None:
    today = date(2026, 9, 7)
    days = {today - timedelta(days=1), today - timedelta(days=2)}
    assert compute_streak(days, today=today) == 2


def test_compute_streak_broken_by_a_gap() -> None:
    today = date(2026, 9, 7)
    days = {today, today - timedelta(days=2)}
    assert compute_streak(days, today=today) == 1


def test_compute_streak_zero_if_last_review_older_than_yesterday() -> None:
    today = date(2026, 9, 7)
    days = {today - timedelta(days=5)}
    assert compute_streak(days, today=today) == 0
