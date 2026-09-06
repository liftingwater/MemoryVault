"""Test Deck CRUD API endpoints."""
import uuid
from datetime import datetime

from fastapi.testclient import TestClient

from app.models import DeckResponse
from tests.conftest import create_test_jwt


# ── Response model ─────────────────────────────────────────────────────────


def test_deck_response_coerces_uuid_id_to_str() -> None:
    """Postgres returns id as uuid.UUID; DeckResponse must coerce it to str."""
    deck_id = uuid.uuid4()
    now = datetime.utcnow()
    resp = DeckResponse(
        id=deck_id,
        name="Deck",
        description=None,
        tags=[],
        created_at=now,
        updated_at=now,
    )
    assert resp.id == str(deck_id)
    assert isinstance(resp.id, str)


# ── Create Deck ────────────────────────────────────────────────────────────


def test_create_deck_requires_auth(client: TestClient) -> None:
    """Test that creating a deck requires authentication."""
    response = client.post("/api/decks", json={"name": "Test Deck"})
    assert response.status_code == 403


def test_create_deck_with_valid_token(client: TestClient) -> None:
    """Test creating a deck with valid token."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    response = client.post(
        "/api/decks",
        json={"name": "My Deck", "description": "Test", "tags": ["learning"]},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Deck"
    assert data["description"] == "Test"
    assert data["tags"] == ["learning"]
    assert "id" in data
    assert "created_at" in data


def test_create_deck_with_minimal_fields(client: TestClient) -> None:
    """Test creating a deck with only required fields."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    response = client.post(
        "/api/decks",
        json={"name": "Minimal Deck"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Minimal Deck"
    assert data["description"] is None
    assert data["tags"] == []


# ── List Decks ─────────────────────────────────────────────────────────────


def test_list_decks_requires_auth(client: TestClient) -> None:
    """Test that listing decks requires authentication."""
    response = client.get("/api/decks")
    assert response.status_code == 403


def test_list_decks_empty(client: TestClient) -> None:
    """Test listing decks when user has none."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    response = client.get(
        "/api/decks",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["decks"] == []


def test_list_decks_isolation(client: TestClient) -> None:
    """Test that users only see their own decks."""
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())
    token1 = create_test_jwt(user1_id)
    token2 = create_test_jwt(user2_id)
    
    # User 1 creates a deck
    client.post(
        "/api/decks",
        json={"name": "User1 Deck"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    
    # User 2 lists their decks - should be empty
    response = client.get(
        "/api/decks",
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    assert response.status_code == 200
    assert response.json()["total"] == 0


# ── Get Deck ────────────────────────────────────────────────────────────────


def test_get_deck_requires_auth(client: TestClient) -> None:
    """Test that getting a deck requires authentication."""
    response = client.get(f"/api/decks/{uuid.uuid4()}")
    assert response.status_code == 403


def test_get_deck_not_found(client: TestClient) -> None:
    """Test getting a non-existent deck."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    response = client.get(
        f"/api/decks/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


def test_get_deck_wrong_owner(client: TestClient) -> None:
    """Test that users cannot access other users' decks."""
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())
    token1 = create_test_jwt(user1_id)
    token2 = create_test_jwt(user2_id)
    
    # User 1 creates a deck
    create_response = client.post(
        "/api/decks",
        json={"name": "Private Deck"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    deck_id = create_response.json()["id"]
    
    # User 2 tries to access it
    response = client.get(
        f"/api/decks/{deck_id}",
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    assert response.status_code == 404


# ── Update Deck ────────────────────────────────────────────────────────────


def test_update_deck_requires_auth(client: TestClient) -> None:
    """Test that updating a deck requires authentication."""
    response = client.put(
        f"/api/decks/{uuid.uuid4()}",
        json={"name": "Updated"}
    )
    assert response.status_code == 403


def test_update_deck_success(client: TestClient) -> None:
    """Test updating a deck successfully."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    # Create deck
    create_response = client.post(
        "/api/decks",
        json={"name": "Original", "description": "Original desc"},
        headers={"Authorization": f"Bearer {token}"}
    )
    deck_id = create_response.json()["id"]
    
    # Update it
    response = client.put(
        f"/api/decks/{deck_id}",
        json={"name": "Updated", "tags": ["new"]},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["tags"] == ["new"]


# ── Delete Deck ────────────────────────────────────────────────────────────


def test_delete_deck_requires_auth(client: TestClient) -> None:
    """Test that deleting a deck requires authentication."""
    response = client.delete(f"/api/decks/{uuid.uuid4()}")
    assert response.status_code == 403


def test_delete_deck_success(client: TestClient) -> None:
    """Test deleting a deck successfully."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    # Create deck
    create_response = client.post(
        "/api/decks",
        json={"name": "To Delete"},
        headers={"Authorization": f"Bearer {token}"}
    )
    deck_id = create_response.json()["id"]
    
    # Delete it
    response = client.delete(
        f"/api/decks/{deck_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 204
    
    # Verify it's gone
    get_response = client.get(
        f"/api/decks/{deck_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 404


def test_delete_deck_not_found(client: TestClient) -> None:
    """Test deleting a non-existent deck."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    response = client.delete(
        f"/api/decks/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
