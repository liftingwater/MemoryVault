"""API-boundary tests for persisted coaching sessions."""
import io
import json
import uuid
from typing import Any, Dict, Generator, cast
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.ai import (
    AICoachError,
    CoachingResponse,
    DeckContextResponse,
    GeneratedOutline,
    GeneratedOutlineItem,
)
from app.services.ai_coach import get_ai_coach
from app.services.context_store import InMemoryContextStore, S3ContextStore, get_context_store
from tests.conftest import create_test_jwt


class FakeCoach:
    def __init__(self, response: CoachingResponse) -> None:
        self.response = response
        self.context_response = DeckContextResponse(context={"learner_goal": "Build APIs"})
        self.calls: list[tuple[Any, Any]] = []

    def generate_response(self, history: Any, context: Any) -> CoachingResponse:
        self.calls.append((history, context))
        return self.response

    def generate_context(self, history: Any, context: Any) -> DeckContextResponse:
        self.calls.append((history, context))
        return self.context_response


class FailingContextStore(InMemoryContextStore):
    def save(self, user_id: str, deck_id: str, context: Any) -> None:
        raise RuntimeError("S3 is unavailable")


class RaisingCoach:
    def generate_response(self, history: Any, context: Any) -> CoachingResponse:
        raise RuntimeError("Bedrock is unavailable")


@pytest.fixture
def coaching_overrides() -> Generator[Dict[str, Any], None, None]:
    app.dependency_overrides.clear()
    store = InMemoryContextStore()
    coach = FakeCoach(CoachingResponse(content="Let's refine that scope."))
    app.dependency_overrides[get_ai_coach] = lambda: coach
    app.dependency_overrides[get_context_store] = lambda: store
    yield {"coach": coach, "store": store}
    app.dependency_overrides.clear()


def _headers(user_id: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {create_test_jwt(user_id)}"}


def _deck(client: TestClient, user_id: str) -> str:
    response = client.post("/api/decks", json={"name": "Python"}, headers=_headers(user_id))
    assert response.status_code == 201
    return cast(str, response.json()["id"])


def _start(client: TestClient, user_id: str, deck_id: str) -> str:
    response = client.post(f"/api/decks/{deck_id}/coaching/start", headers=_headers(user_id))
    assert response.status_code == 201
    assert response.json()["assistant_message"]["content"] == "What is your learning goal for this deck?"
    return cast(str, response.json()["session"]["id"])


def test_start_persists_first_intake_question_and_history(client: TestClient, coaching_overrides: Dict[str, Any]) -> None:
    user_id = str(uuid.uuid4())
    deck_id = _deck(client, user_id)
    session_id = _start(client, user_id, deck_id)

    response = client.get(f"/api/coaching/{session_id}", headers=_headers(user_id))

    assert response.status_code == 200
    assert response.json()["session"]["status"] == "active"
    assert [message["content"] for message in response.json()["messages"]] == [
        "What is your learning goal for this deck?"
    ]


def test_intake_then_free_chat_persists_generated_outline(client: TestClient, coaching_overrides: Dict[str, Any]) -> None:
    user_id = str(uuid.uuid4())
    deck_id = _deck(client, user_id)
    session_id = _start(client, user_id, deck_id)
    coaching_overrides["coach"].response = CoachingResponse(
        content="What part of API design should we refine first?"
    )

    first = client.post(f"/api/coaching/{session_id}/message", json={"content": "Build APIs"}, headers=_headers(user_id))
    second = client.post(f"/api/coaching/{session_id}/message", json={"content": "I know syntax"}, headers=_headers(user_id))
    third = client.post(f"/api/coaching/{session_id}/message", json={"content": "Three hours"}, headers=_headers(user_id))

    assert first.json()["assistant_message"]["content"] == "What do you already know about this subject?"
    assert second.json()["assistant_message"]["content"] == "How much time can you commit to studying each week?"
    assert third.status_code == 200
    assert third.json()["assistant_message"]["content"] == "What part of API design should we refine first?"
    assert third.json()["outline"] is None

    coaching_overrides["coach"].response = CoachingResponse(
        content="Here is a focused outline.",
        outline=GeneratedOutline(items=[
            GeneratedOutlineItem(section="Basics", title="Variables", description="Name values"),
            GeneratedOutlineItem(section="Basics", title="Functions"),
        ]),
    )
    fourth = client.post(
        f"/api/coaching/{session_id}/message",
        json={"content": "Focus on REST APIs."},
        headers=_headers(user_id),
    )

    assert fourth.status_code == 200
    assert fourth.json()["assistant_message"]["content"] == "Here is a focused outline."
    assert fourth.json()["outline"]["items"][0]["title"] == "Variables"
    assert len(coaching_overrides["coach"].calls) == 2

    outline = client.get(f"/api/decks/{deck_id}/outline", headers=_headers(user_id))
    history = client.get(f"/api/coaching/{session_id}", headers=_headers(user_id))
    assert outline.json()["outline"]["items"][1]["title"] == "Functions"
    assert [message["role"] for message in history.json()["messages"]] == [
        "assistant", "user", "assistant", "user", "assistant", "user", "assistant", "user", "assistant"
    ]


def test_provider_error_is_a_success_response_and_keeps_user_message(client: TestClient, coaching_overrides: Dict[str, Any]) -> None:
    user_id = str(uuid.uuid4())
    deck_id = _deck(client, user_id)
    session_id = _start(client, user_id, deck_id)
    coaching_overrides["coach"].response = CoachingResponse(error=AICoachError(code="timeout", message="Try again."))
    for answer in ("A goal", "Some knowledge"):
        client.post(f"/api/coaching/{session_id}/message", json={"content": answer}, headers=_headers(user_id))

    response = client.post(f"/api/coaching/{session_id}/message", json={"content": "Two hours"}, headers=_headers(user_id))
    history = client.get(f"/api/coaching/{session_id}", headers=_headers(user_id))

    assert response.status_code == 200
    assert response.json()["error"] == {"code": "timeout", "message": "Try again."}
    assert history.json()["messages"][-1]["content"] == "Two hours"
    assert len(history.json()["messages"]) == 6


def test_unexpected_provider_error_does_not_crash_and_keeps_user_message(client: TestClient, coaching_overrides: Dict[str, Any]) -> None:
    user_id = str(uuid.uuid4())
    deck_id = _deck(client, user_id)
    session_id = _start(client, user_id, deck_id)
    app.dependency_overrides[get_ai_coach] = RaisingCoach
    for answer in ("A goal", "Some knowledge"):
        client.post(f"/api/coaching/{session_id}/message", json={"content": answer}, headers=_headers(user_id))

    response = client.post(f"/api/coaching/{session_id}/message", json={"content": "Two hours"}, headers=_headers(user_id))
    history = client.get(f"/api/coaching/{session_id}", headers=_headers(user_id))

    assert response.status_code == 200
    assert response.json()["error"]["code"] == "service_unavailable"
    assert history.json()["messages"][-1]["content"] == "Two hours"


def test_start_archives_previous_session_and_enforces_owner(client: TestClient, coaching_overrides: Dict[str, Any]) -> None:
    owner_id, other_id = str(uuid.uuid4()), str(uuid.uuid4())
    deck_id = _deck(client, owner_id)
    first_session = _start(client, owner_id, deck_id)
    second_session = _start(client, owner_id, deck_id)

    sessions = client.get(f"/api/decks/{deck_id}/coaching/sessions", headers=_headers(owner_id))
    forbidden_history = client.get(f"/api/coaching/{second_session}", headers=_headers(other_id))
    forbidden_deck = client.get(f"/api/decks/{deck_id}/coaching/sessions", headers=_headers(other_id))
    archived_message = client.post(f"/api/coaching/{first_session}/message", json={"content": "hello"}, headers=_headers(owner_id))

    assert [session["status"] for session in sessions.json()["sessions"]] == ["active", "archived"]
    assert forbidden_history.status_code == 404
    assert forbidden_deck.status_code == 404
    assert archived_message.status_code == 409


def test_end_archives_session_and_reports_context_store_failure(client: TestClient, coaching_overrides: Dict[str, Any]) -> None:
    user_id = str(uuid.uuid4())
    deck_id = _deck(client, user_id)
    session_id = _start(client, user_id, deck_id)
    failing_store = FailingContextStore()
    app.dependency_overrides[get_context_store] = lambda: failing_store

    response = client.post(f"/api/coaching/{session_id}/end", headers=_headers(user_id))
    history = client.get(f"/api/coaching/{session_id}", headers=_headers(user_id))

    assert response.status_code == 200
    assert response.json()["session"]["status"] == "archived"
    assert response.json()["context_saved"] is False
    assert response.json()["error"]["code"] == "context_store_unavailable"
    assert history.json()["session"]["status"] == "archived"


def test_end_saves_context_at_user_deck_key(client: TestClient, coaching_overrides: Dict[str, Any]) -> None:
    user_id = str(uuid.uuid4())
    deck_id = _deck(client, user_id)
    session_id = _start(client, user_id, deck_id)
    coaching_overrides["store"].values[f"{user_id}/{deck_id}/context.json"] = {"goal": "APIs"}

    response = client.post(f"/api/coaching/{session_id}/end", headers=_headers(user_id))

    assert response.status_code == 200
    assert response.json()["context_saved"] is True
    assert response.json()["error"] is None
    assert coaching_overrides["store"].values[f"{user_id}/{deck_id}/context.json"] == {
        "goal": "APIs",
        "learner_goal": "Build APIs",
    }


def test_end_reports_ai_error_after_archiving(client: TestClient, coaching_overrides: Dict[str, Any]) -> None:
    user_id = str(uuid.uuid4())
    deck_id = _deck(client, user_id)
    session_id = _start(client, user_id, deck_id)
    coaching_overrides["coach"].context_response = DeckContextResponse(
        error=AICoachError(code="service_unavailable", message="Bedrock is unavailable.")
    )

    response = client.post(f"/api/coaching/{session_id}/end", headers=_headers(user_id))

    assert response.status_code == 200
    assert response.json()["session"]["status"] == "archived"
    assert response.json()["context_saved"] is False
    assert response.json()["error"]["code"] == "service_unavailable"


def test_end_reports_an_unexpected_ai_error_after_archiving(client: TestClient, coaching_overrides: Dict[str, Any]) -> None:
    user_id = str(uuid.uuid4())
    deck_id = _deck(client, user_id)
    session_id = _start(client, user_id, deck_id)
    app.dependency_overrides[get_ai_coach] = RaisingCoach

    response = client.post(f"/api/coaching/{session_id}/end", headers=_headers(user_id))

    assert response.status_code == 200
    assert response.json()["session"]["status"] == "archived"
    assert response.json()["context_saved"] is False
    assert response.json()["error"]["code"] == "service_unavailable"


def test_message_rejects_whitespace_only_content(client: TestClient, coaching_overrides: Dict[str, Any]) -> None:
    user_id = str(uuid.uuid4())
    deck_id = _deck(client, user_id)
    session_id = _start(client, user_id, deck_id)

    response = client.post(
        f"/api/coaching/{session_id}/message",
        json={"content": "   "},
        headers=_headers(user_id),
    )

    assert response.status_code == 422


def test_s3_context_store_reads_and_writes_the_deck_context_key() -> None:
    client = MagicMock()
    client.get_object.return_value = {"Body": io.BytesIO(b'{"goal": "Build APIs"}')}
    store = S3ContextStore(bucket="deck-contexts", client=client)

    assert store.load("user-1", "deck-1") == {"goal": "Build APIs"}
    store.save("user-1", "deck-1", {"goal": "Ship an API"})

    client.get_object.assert_called_once_with(
        Bucket="deck-contexts", Key="user-1/deck-1/context.json"
    )
    write = client.put_object.call_args.kwargs
    assert write["Bucket"] == "deck-contexts"
    assert write["Key"] == "user-1/deck-1/context.json"
    assert write["ContentType"] == "application/json"
    assert json.loads(write["Body"]) == {"goal": "Ship an API"}


@pytest.mark.parametrize("method,path,body", [
    ("post", "/api/decks/not-a-deck/coaching/start", None),
    ("post", "/api/coaching/not-a-session/message", {"content": "hello"}),
    ("get", "/api/decks/not-a-deck/coaching/sessions", None),
    ("get", "/api/coaching/not-a-session", None),
    ("post", "/api/coaching/not-a-session/end", None),
    ("get", "/api/decks/not-a-deck/outline", None),
])
def test_coaching_endpoints_require_auth(client: TestClient, method: str, path: str, body: Any) -> None:
    response = getattr(client, method)(path, json=body) if body else getattr(client, method)(path)
    assert response.status_code == 403