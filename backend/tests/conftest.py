import os
from typing import Any
from unittest import mock
import sys

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

# Patch database before importing app
from tests.test_database import mock_get_db, _reset_test_data  # noqa: E402
import app.database  # noqa: E402
app.database.get_db = mock_get_db

from app.main import app as fastapi_app  # noqa: E402


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
