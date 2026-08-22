"""Test authentication and JWT validation."""

import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app.auth import decode_jwt, AuthError
from app.config import settings


def create_test_jwt(user_id: str, email: str = "test@example.com", expired: bool = False) -> str:
    """Create a valid JWT token for testing."""
    now = datetime.now(timezone.utc)
    exp_time = now + (timedelta(hours=-1) if expired else timedelta(hours=1))

    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(exp_time.timestamp()),
        "aud": "authenticated",
    }

    token = jwt.encode(
        payload,
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )
    return token


def test_auth_decodes_valid_jwt() -> None:
    """Test that valid JWT tokens are decoded correctly."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)

    payload = decode_jwt(token)

    assert payload["sub"] == user_id
    assert payload["email"] == "test@example.com"


def test_auth_rejects_expired_token() -> None:
    """Test that expired tokens are rejected."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id, expired=True)

    with pytest.raises(AuthError, match="expired"):
        decode_jwt(token)


def test_auth_rejects_invalid_signature() -> None:
    """Test that tokens with invalid signatures are rejected."""
    user_id = str(uuid.uuid4())

    # Create token with wrong secret
    payload = {
        "sub": user_id,
        "email": "test@example.com",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }

    token = jwt.encode(payload, "wrong_secret", algorithm="HS256")

    with pytest.raises(AuthError, match="Invalid"):
        decode_jwt(token)


# ── API endpoint auth tests ─────────────────────────────────────────────────


def test_dashboard_returns_403_without_auth(client: TestClient) -> None:
    """Test that /dashboard returns 403 when no auth header is provided."""
    # HTTPBearer dependency returns 403 for missing credentials, not 401
    response = client.get("/dashboard")
    assert response.status_code == 403


def test_dashboard_returns_401_with_invalid_token(client: TestClient) -> None:
    """Test that /dashboard returns 401 with invalid token."""
    response = client.get(
        "/dashboard",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


def test_dashboard_returns_200_with_valid_token(client: TestClient) -> None:
    """Test that /dashboard returns 200 with valid JWT."""
    user_id = str(uuid.uuid4())
    email = "test@example.com"
    token = create_test_jwt(user_id, email)

    response = client.get(
        "/dashboard",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert data["email"] == email
    assert "Welcome" in data["message"]


def test_dashboard_returns_401_with_expired_token(client: TestClient) -> None:
    """Test that /dashboard returns 401 with expired token."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id, expired=True)

    response = client.get(
        "/dashboard",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
    assert "expired" in response.json()["detail"]
