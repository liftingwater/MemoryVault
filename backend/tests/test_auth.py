"""Test authentication and JWT validation."""

import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app.auth import decode_jwt, AuthError
from tests.conftest import create_test_jwt


def test_auth_decodes_valid_jwt() -> None:
    """Test that valid ES256 JWT tokens are decoded correctly."""
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
    """Test that a token signed by a different key is rejected."""
    other_key = ec.generate_private_key(ec.SECP256R1())
    payload = {
        "sub": str(uuid.uuid4()),
        "email": "test@example.com",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        "aud": "authenticated",
    }
    token = jwt.encode(payload, other_key, algorithm="ES256")

    with pytest.raises(AuthError, match="Invalid"):
        decode_jwt(token)


def test_auth_rejects_non_es256_algorithm() -> None:
    """Test that non-ES256 tokens (e.g. HS256) are rejected outright."""
    payload = {
        "sub": str(uuid.uuid4()),
        "email": "test@example.com",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        "aud": "authenticated",
    }
    token = jwt.encode(payload, "some-shared-secret", algorithm="HS256")

    with pytest.raises(AuthError, match="Invalid"):
        decode_jwt(token)


# ── API endpoint auth tests ─────────────────────────────────────────────────


def test_dashboard_returns_403_without_auth(client: TestClient) -> None:
    """Test that /api/dashboard returns 403 when no auth header is provided."""
    # HTTPBearer dependency returns 403 for missing credentials, not 401
    response = client.get("/api/dashboard")
    assert response.status_code == 403


def test_dashboard_returns_401_with_invalid_token(client: TestClient) -> None:
    """Test that /api/dashboard returns 401 with invalid token."""
    response = client.get(
        "/api/dashboard",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


def test_dashboard_returns_200_with_valid_token(client: TestClient) -> None:
    """Test that /api/dashboard returns 200 with valid JWT."""
    user_id = str(uuid.uuid4())
    email = "test@example.com"
    token = create_test_jwt(user_id, email)

    response = client.get(
        "/api/dashboard",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert data["email"] == email
    assert "Welcome" in data["message"]


def test_dashboard_returns_401_with_expired_token(client: TestClient) -> None:
    """Test that /api/dashboard returns 401 with expired token."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id, expired=True)

    response = client.get(
        "/api/dashboard",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
    assert "expired" in response.json()["detail"]
