import os
import pytest
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

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
