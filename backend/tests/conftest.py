import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

# Load environment variables from .env for testing
def load_env_vars() -> None:
    """Load environment variables from backend/.env file."""
    env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Remove quotes if present
                    value = value.strip("'\"")
                    os.environ[key] = value


load_env_vars()

# Patch database before importing app
from tests.test_database import mock_get_db, _reset_test_data  # noqa: E402
import app.database  # noqa: E402
app.database.get_db = mock_get_db

from app.main import app as fastapi_app  # noqa: E402

# ── ES256 test signing key ───────────────────────────────────────────────────
# Production verifies Supabase's ES256 tokens against the project's JWKS. Tests
# mint real ES256 tokens with an ephemeral P-256 keypair and point the JWKS
# lookup at the matching public key, so the verification path exercised here is
# exactly the one used in production (only the network fetch is stubbed).
_TEST_SIGNING_KEY = ec.generate_private_key(ec.SECP256R1())


def create_test_jwt(
    user_id: str, email: str = "test@example.com", expired: bool = False
) -> str:
    """Create a valid ES256 JWT signed with the test key."""
    now = datetime.now(timezone.utc)
    exp_time = now + (timedelta(hours=-1) if expired else timedelta(hours=1))
    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(exp_time.timestamp()),
        "aud": "authenticated",
    }
    return jwt.encode(
        payload,
        _TEST_SIGNING_KEY,
        algorithm="ES256",
        headers={"kid": "test-ec-key"},
    )


@pytest.fixture(autouse=True)
def mock_jwks(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Point the JWKS lookup at the test public key instead of the network."""
    public_key = _TEST_SIGNING_KEY.public_key()
    fake_client = SimpleNamespace(
        get_signing_key_from_jwt=lambda token: SimpleNamespace(key=public_key)
    )
    monkeypatch.setattr("app.auth._get_jwks_client", lambda: fake_client)
    yield


@pytest.fixture
def client() -> TestClient:
    """Create a test client with mocked database."""
    _reset_test_data()
    return TestClient(fastapi_app)


@pytest.fixture(autouse=True)
def reset_test_data_fixture() -> Any:
    """Reset test data before and after each test."""
    _reset_test_data()
    yield
    _reset_test_data()
