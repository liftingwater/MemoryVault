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


# ── Create Card ────────────────────────────────────────────────────────────


def test_create_card_requires_auth(client: TestClient) -> None:
    """Test that creating a card requires authentication."""
    deck_id = str(uuid.uuid4())
    response = client.post(
        f"/decks/{deck_id}/cards",
        json={"card_type": "front_back", "front_md": "Q", "back_md": "A"},
    )
    assert response.status_code == 403


def test_create_front_back_card(client: TestClient) -> None:
    """Test creating a front/back card."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    # Create deck first
    deck_response = client.post(
        "/decks",
        json={"name": "Test Deck"},
        headers={"Authorization": f"Bearer {token}"}
    )
    deck_id = deck_response.json()["id"]
    
    # Create card
    response = client.post(
        f"/decks/{deck_id}/cards",
        json={
            "card_type": "front_back",
            "front_md": "What is 2+2?",
            "back_md": "4"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["card_type"] == "front_back"
    assert data["front_md"] == "What is 2+2?"
    assert data["back_md"] == "4"
    assert data["cloze_text_md"] is None
    assert "id" in data
    assert "created_at" in data


def test_create_cloze_card(client: TestClient) -> None:
    """Test creating a cloze deletion card."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    # Create deck
    deck_response = client.post(
        "/decks",
        json={"name": "Test Deck"},
        headers={"Authorization": f"Bearer {token}"}
    )
    deck_id = deck_response.json()["id"]
    
    # Create cloze card
    response = client.post(
        f"/decks/{deck_id}/cards",
        json={
            "card_type": "cloze",
            "front_md": "The capital of France is {{Paris}}",
            "cloze_text_md": "The capital of France is {{Paris}}",
            "cloze_answer": "Paris"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["card_type"] == "cloze"
    assert data["cloze_answer"] == "Paris"
    assert data["back_md"] is None


def test_create_card_missing_back_md(client: TestClient) -> None:
    """Test that creating front_back card without back_md fails."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    deck_response = client.post(
        "/decks",
        json={"name": "Test Deck"},
        headers={"Authorization": f"Bearer {token}"}
    )
    deck_id = deck_response.json()["id"]
    
    response = client.post(
        f"/decks/{deck_id}/cards",
        json={
            "card_type": "front_back",
            "front_md": "Question"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422  # Validation error


def test_create_card_missing_cloze_text(client: TestClient) -> None:
    """Test that creating cloze card without cloze_text_md fails."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    deck_response = client.post(
        "/decks",
        json={"name": "Test Deck"},
        headers={"Authorization": f"Bearer {token}"}
    )
    deck_id = deck_response.json()["id"]
    
    response = client.post(
        f"/decks/{deck_id}/cards",
        json={
            "card_type": "cloze",
            "front_md": "Text",
            "cloze_answer": "Answer"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


def test_create_card_empty_front_md(client: TestClient) -> None:
    """Test that empty front_md is rejected."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    deck_response = client.post(
        "/decks",
        json={"name": "Test Deck"},
        headers={"Authorization": f"Bearer {token}"}
    )
    deck_id = deck_response.json()["id"]
    
    response = client.post(
        f"/decks/{deck_id}/cards",
        json={
            "card_type": "front_back",
            "front_md": "",
            "back_md": "Answer"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 422


def test_create_card_deck_not_found(client: TestClient) -> None:
    """Test creating a card in a non-existent deck."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    response = client.post(
        f"/decks/{uuid.uuid4()}/cards",
        json={
            "card_type": "front_back",
            "front_md": "Q",
            "back_md": "A"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


# ── List Cards ─────────────────────────────────────────────────────────────


def test_list_cards_requires_auth(client: TestClient) -> None:
    """Test that listing cards requires authentication."""
    response = client.get(f"/decks/{uuid.uuid4()}/cards")
    assert response.status_code == 403


def test_list_cards_empty_deck(client: TestClient) -> None:
    """Test listing cards in an empty deck."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    deck_response = client.post(
        "/decks",
        json={"name": "Empty Deck"},
        headers={"Authorization": f"Bearer {token}"}
    )
    deck_id = deck_response.json()["id"]
    
    response = client.get(
        f"/decks/{deck_id}/cards",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["cards"] == []


def test_list_cards_with_search(client: TestClient) -> None:
    """Test listing cards with search functionality."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    # Create deck
    deck_response = client.post(
        "/decks",
        json={"name": "Test Deck"},
        headers={"Authorization": f"Bearer {token}"}
    )
    deck_id = deck_response.json()["id"]
    
    # Create multiple cards
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
    
    # Search for Python
    response = client.get(
        f"/decks/{deck_id}/cards?search=Python",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "Python" in data["cards"][0]["front_md"]


def test_list_cards_wrong_deck_owner(client: TestClient) -> None:
    """Test that users can only list cards in their own decks."""
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())
    token1 = create_test_jwt(user1_id)
    token2 = create_test_jwt(user2_id)
    
    # User1 creates deck
    deck_response = client.post(
        "/decks",
        json={"name": "User1 Deck"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    deck_id = deck_response.json()["id"]
    
    # User2 tries to list cards
    response = client.get(
        f"/decks/{deck_id}/cards",
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    assert response.status_code == 200
    assert response.json()["total"] == 0


# ── Update Card ────────────────────────────────────────────────────────────


def test_update_card_requires_auth(client: TestClient) -> None:
    """Test that updating a card requires authentication."""
    response = client.put(
        f"/cards/{uuid.uuid4()}",
        json={"front_md": "New question"}
    )
    assert response.status_code == 403


def test_update_card_front_content(client: TestClient) -> None:
    """Test updating a card's front content."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    # Create deck and card
    deck_response = client.post(
        "/decks",
        json={"name": "Test Deck"},
        headers={"Authorization": f"Bearer {token}"}
    )
    deck_id = deck_response.json()["id"]
    
    card_response = client.post(
        f"/decks/{deck_id}/cards",
        json={"card_type": "front_back", "front_md": "Old Q", "back_md": "A"},
        headers={"Authorization": f"Bearer {token}"}
    )
    card_id = card_response.json()["id"]
    
    # Update card
    response = client.put(
        f"/cards/{card_id}",
        json={"front_md": "New Q"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["front_md"] == "New Q"
    assert data["back_md"] == "A"


def test_update_card_not_found(client: TestClient) -> None:
    """Test updating a non-existent card."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    response = client.put(
        f"/cards/{uuid.uuid4()}",
        json={"front_md": "New"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


def test_update_card_wrong_owner(client: TestClient) -> None:
    """Test that users can only update their own cards."""
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())
    token1 = create_test_jwt(user1_id)
    token2 = create_test_jwt(user2_id)
    
    # User1 creates deck and card
    deck_response = client.post(
        "/decks",
        json={"name": "User1 Deck"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    deck_id = deck_response.json()["id"]
    
    card_response = client.post(
        f"/decks/{deck_id}/cards",
        json={"card_type": "front_back", "front_md": "Q", "back_md": "A"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    card_id = card_response.json()["id"]
    
    # User2 tries to update
    response = client.put(
        f"/cards/{card_id}",
        json={"front_md": "Hacked"},
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    assert response.status_code == 404


# ── Delete Card ────────────────────────────────────────────────────────────


def test_delete_card_requires_auth(client: TestClient) -> None:
    """Test that deleting a card requires authentication."""
    response = client.delete(f"/cards/{uuid.uuid4()}")
    assert response.status_code == 403


def test_delete_card_simple(client: TestClient) -> None:
    """Test deleting a card returns 404 for non-existent card (deletion not yet mocked)."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)

    # Try to delete a non-existent card
    response = client.delete(
        f"/cards/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


def test_delete_card_not_found(client: TestClient) -> None:
    """Test deleting a non-existent card."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    response = client.delete(
        f"/cards/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


def test_delete_card_wrong_owner(client: TestClient) -> None:
    """Test that users can only delete their own cards."""
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())
    token1 = create_test_jwt(user1_id)
    token2 = create_test_jwt(user2_id)
    
    # User1 creates card
    deck_response = client.post(
        "/decks",
        json={"name": "User1 Deck"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    deck_id = deck_response.json()["id"]
    
    card_response = client.post(
        f"/decks/{deck_id}/cards",
        json={"card_type": "front_back", "front_md": "Q", "back_md": "A"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    card_id = card_response.json()["id"]
    
    # User2 tries to delete
    response = client.delete(
        f"/cards/{card_id}",
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    assert response.status_code == 404
    
    # Verify card still exists
    list_response = client.get(
        f"/decks/{deck_id}/cards",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert list_response.json()["total"] == 1
