from fastapi.testclient import TestClient

from app.config import settings


def test_health_allows_frontend_origin(client: TestClient) -> None:
    origin = settings.allowed_origins[0]

    response = client.get("/health", headers={"Origin": origin})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_health_omits_cors_header_for_unknown_origin(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "https://evil.example"})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
