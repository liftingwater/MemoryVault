"""Test Deck CRUD API endpoints."""
import uuid

from fastapi.testclient import TestClient

from tests.conftest import create_test_jwt


# ── Create Deck ────────────────────────────────────────────────────────────


def test_create_deck_requires_auth(client: TestClient) -> None:
    """Test that creating a deck requires authentication."""
    response = client.post("/decks", json={"name": "Test Deck"})
    assert response.status_code == 403


def test_create_deck_with_valid_token(client: TestClient) -> None:
    """Test creating a deck with valid token."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    response = client.post(
        "/decks",
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
        "/decks",
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
    response = client.get("/decks")
    assert response.status_code == 403


def test_list_decks_empty(client: TestClient) -> None:
    """Test listing decks when user has none."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    response = client.get(
        "/decks",
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
        "/decks",
        json={"name": "User1 Deck"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    
    # User 2 lists their decks - should be empty
    response = client.get(
        "/decks",
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    assert response.status_code == 200
    assert response.json()["total"] == 0


# ── Get Deck ────────────────────────────────────────────────────────────────


def test_get_deck_requires_auth(client: TestClient) -> None:
    """Test that getting a deck requires authentication."""
    response = client.get(f"/decks/{uuid.uuid4()}")
    assert response.status_code == 403


def test_get_deck_not_found(client: TestClient) -> None:
    """Test getting a non-existent deck."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    response = client.get(
        f"/decks/{uuid.uuid4()}",
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
        "/decks",
        json={"name": "Private Deck"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    deck_id = create_response.json()["id"]
    
    # User 2 tries to access it
    response = client.get(
        f"/decks/{deck_id}",
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    assert response.status_code == 404


# ── Update Deck ────────────────────────────────────────────────────────────


def test_update_deck_requires_auth(client: TestClient) -> None:
    """Test that updating a deck requires authentication."""
    response = client.put(
        f"/decks/{uuid.uuid4()}",
        json={"name": "Updated"}
    )
    assert response.status_code == 403


def test_update_deck_success(client: TestClient) -> None:
    """Test updating a deck successfully."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    # Create deck
    create_response = client.post(
        "/decks",
        json={"name": "Original", "description": "Original desc"},
        headers={"Authorization": f"Bearer {token}"}
    )
    deck_id = create_response.json()["id"]
    
    # Update it
    response = client.put(
        f"/decks/{deck_id}",
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
    response = client.delete(f"/decks/{uuid.uuid4()}")
    assert response.status_code == 403


def test_delete_deck_success(client: TestClient) -> None:
    """Test deleting a deck successfully."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    # Create deck
    create_response = client.post(
        "/decks",
        json={"name": "To Delete"},
        headers={"Authorization": f"Bearer {token}"}
    )
    deck_id = create_response.json()["id"]
    
    # Delete it
    response = client.delete(
        f"/decks/{deck_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 204
    
    # Verify it's gone
    get_response = client.get(
        f"/decks/{deck_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 404


def test_delete_deck_not_found(client: TestClient) -> None:
    """Test deleting a non-existent deck."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    
    response = client.delete(
        f"/decks/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
