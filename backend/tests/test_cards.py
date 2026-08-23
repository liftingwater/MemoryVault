"""Test Card CRUD API endpoints."""
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app.config import settings


def create_test_jwt(user_id: str, email: str = "test@example.com") -> str:
    """Create a valid JWT token for testing."""
    now = datetime.now(timezone.utc)
    exp_time = now + timedelta(hours=1)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(exp_time.timestamp()),
        "aud": "authenticated",
    }
    return jwt.encode(payload, settings.supabase_jwt_secret, algorithm="HS256")


def create_deck(client: TestClient, token: str, name: str = "Test Deck") -> str:
    """Helper to create a deck and return its ID."""
    response = client.post(
        "/decks",
        json={"name": name, "description": "Test deck", "tags": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    return response.json()["id"]


# ── Create Card ────────────────────────────────────────────────────────────

def test_create_card_requires_auth(client: TestClient) -> None:
    """Test that creating a card requires authentication."""
    response = client.post("/decks/test-deck/cards", json={"card_type": "front_back", "front_md": "Q"})
    assert response.status_code == 403


def test_create_front_back_card(client: TestClient) -> None:
    """Test creating a front/back card."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    deck_id = create_deck(client, token)

    response = client.post(
        f"/decks/{deck_id}/cards",
        json={"card_type": "front_back", "front_md": "Question?", "back_md": "Answer"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    card = response.json()
    assert card["card_type"] == "front_back"
    assert card["front_md"] == "Question?"
    assert card["back_md"] == "Answer"


def test_create_cloze_card(client: TestClient) -> None:
    """Test creating a cloze card."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    deck_id = create_deck(client, token)

    response = client.post(
        f"/decks/{deck_id}/cards",
        json={"card_type": "cloze", "cloze_text_md": "The capital of France is {{Paris}}", "cloze_answer": "Paris"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    card = response.json()
    assert card["card_type"] == "cloze"
    assert card["cloze_text_md"] == "The capital of France is {{Paris}}"
    assert card["cloze_answer"] == "Paris"


def test_create_card_empty_front_rejected(client: TestClient) -> None:
    """Test that empty front_md is rejected."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    deck_id = create_deck(client, token)

    response = client.post(
        f"/decks/{deck_id}/cards",
        json={"card_type": "front_back", "front_md": "", "back_md": "Answer"},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Pydantic validation returns 422 for validation errors
    assert response.status_code == 422


def test_create_card_missing_cloze_text_rejected(client: TestClient) -> None:
    """Test that missing cloze_text_md is rejected."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    deck_id = create_deck(client, token)

    response = client.post(
        f"/decks/{deck_id}/cards",
        json={"card_type": "cloze", "cloze_answer": "Paris"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400


def test_create_card_nonexistent_deck(client: TestClient) -> None:
    """Test creating a card in a nonexistent deck."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)

    response = client.post(
        f"/decks/nonexistent-deck-id/cards",
        json={"card_type": "front_back", "front_md": "Q", "back_md": "A"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


# ── List Cards ─────────────────────────────────────────────────────────────

def test_list_cards_empty(client: TestClient) -> None:
    """Test listing cards in an empty deck."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    deck_id = create_deck(client, token)

    response = client.get(
        f"/decks/{deck_id}/cards",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["cards"] == []


def test_list_cards_multiple(client: TestClient) -> None:
    """Test listing multiple cards."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    deck_id = create_deck(client, token)

    # Create two cards
    client.post(
        f"/decks/{deck_id}/cards",
        json={"card_type": "front_back", "front_md": "Q1", "back_md": "A1"},
        headers={"Authorization": f"Bearer {token}"}
    )
    client.post(
        f"/decks/{deck_id}/cards",
        json={"card_type": "front_back", "front_md": "Q2", "back_md": "A2"},
        headers={"Authorization": f"Bearer {token}"}
    )

    response = client.get(
        f"/decks/{deck_id}/cards",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["cards"]) == 2


def test_list_cards_with_search(client: TestClient) -> None:
    """Test listing cards with search filter."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    deck_id = create_deck(client, token)

    client.post(
        f"/decks/{deck_id}/cards",
        json={"card_type": "front_back", "front_md": "Python question", "back_md": "Answer"},
        headers={"Authorization": f"Bearer {token}"}
    )
    client.post(
        f"/decks/{deck_id}/cards",
        json={"card_type": "front_back", "front_md": "Java question", "back_md": "Answer"},
        headers={"Authorization": f"Bearer {token}"}
    )

    response = client.get(
        f"/decks/{deck_id}/cards?search=Python",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


def test_list_cards_unauthorized_deck(client: TestClient) -> None:
    """Test listing cards in a deck owned by another user."""
    user1_id = str(uuid.uuid4())
    token1 = create_test_jwt(user1_id)
    deck_id = create_deck(client, token1)

    user2_id = str(uuid.uuid4())
    token2 = create_test_jwt(user2_id)

    response = client.get(
        f"/decks/{deck_id}/cards",
        headers={"Authorization": f"Bearer {token2}"}
    )

    assert response.status_code == 404



# ── Update Card ────────────────────────────────────────────────────────────

def test_update_card_requires_auth(client: TestClient) -> None:
    """Test that updating a card requires authentication."""
    response = client.put("/decks/cards/test-id", json={"front_md": "Updated"})
    assert response.status_code == 403


def test_update_card_front_back(client: TestClient) -> None:
    """Test updating a front/back card."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    deck_id = create_deck(client, token)

    # Create card
    create_response = client.post(
        f"/decks/{deck_id}/cards",
        json={"card_type": "front_back", "front_md": "Original Q", "back_md": "Original A"},
        headers={"Authorization": f"Bearer {token}"}
    )
    card_id = create_response.json()["id"]

    # Update card
    response = client.put(
        f"/decks/cards/{card_id}",
        json={"front_md": "Updated Q", "back_md": "Updated A"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["front_md"] == "Updated Q"
    assert updated["back_md"] == "Updated A"


def test_delete_card_requires_auth(client: TestClient) -> None:
    """Test that deleting a card requires authentication."""
    response = client.delete("/decks/cards/test-id")
    assert response.status_code == 403


def test_delete_card(client: TestClient) -> None:
    """Test deleting a card."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    deck_id = create_deck(client, token)

    # Create card
    create_response = client.post(
        f"/decks/{deck_id}/cards",
        json={"card_type": "front_back", "front_md": "Q", "back_md": "A"},
        headers={"Authorization": f"Bearer {token}"}
    )
    card_id = create_response.json()["id"]

    # Delete card
    response = client.delete(
        f"/decks/cards/{card_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 204

    # Verify card is gone
    list_response = client.get(
        f"/decks/{deck_id}/cards",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert list_response.json()["total"] == 0


def test_update_card_nonexistent(client: TestClient) -> None:
    """Test updating a nonexistent card."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)

    response = client.put(
        "/decks/cards/nonexistent-id",
        json={"front_md": "Updated"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


def test_delete_card_nonexistent(client: TestClient) -> None:
    """Test deleting a nonexistent card."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)

    response = client.delete(
        "/decks/cards/nonexistent-id",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


def test_update_card_unauthorized(client: TestClient) -> None:
    """Test updating a card in a deck owned by another user."""
    user1_id = str(uuid.uuid4())
    token1 = create_test_jwt(user1_id)
    deck_id = create_deck(client, token1)

    # Create card as user1
    create_response = client.post(
        f"/decks/{deck_id}/cards",
        json={"card_type": "front_back", "front_md": "Q", "back_md": "A"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    card_id = create_response.json()["id"]

    # Try to update as user2
    user2_id = str(uuid.uuid4())
    token2 = create_test_jwt(user2_id)

    response = client.put(
        f"/decks/cards/{card_id}",
        json={"front_md": "Hacked Q"},
        headers={"Authorization": f"Bearer {token2}"}
    )

    assert response.status_code == 403


def test_delete_card_unauthorized(client: TestClient) -> None:
    """Test deleting a card in a deck owned by another user."""
    user1_id = str(uuid.uuid4())
    token1 = create_test_jwt(user1_id)
    deck_id = create_deck(client, token1)

    # Create card as user1
    create_response = client.post(
        f"/decks/{deck_id}/cards",
        json={"card_type": "front_back", "front_md": "Q", "back_md": "A"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    card_id = create_response.json()["id"]

    # Try to delete as user2
    user2_id = str(uuid.uuid4())
    token2 = create_test_jwt(user2_id)

    response = client.delete(
        f"/decks/cards/{card_id}",
        headers={"Authorization": f"Bearer {token2}"}
    )

    assert response.status_code == 403
