"""Unit tests for the provider-neutral AI coaching service interface."""
import io
import json
from dataclasses import replace
from unittest.mock import MagicMock

from botocore.exceptions import ClientError, ConnectTimeoutError, ReadTimeoutError
import pytest

from app.config import settings
from app.models.ai import CoachingMessage
from app.services import ai_coach
from app.services.ai_coach import BedrockAICoach, MockAICoach


def test_mock_ai_coach_returns_its_canned_response() -> None:
    coach = MockAICoach(canned_response="What would you like to learn first?")

    response = coach.generate_response(
        [CoachingMessage(role="user", content="Help me learn Python.")],
        {"goal": "Learn Python fundamentals"},
    )

    assert response.content == "What would you like to learn first?"
    assert response.error is None


def test_bedrock_ai_coach_returns_claude_text_response() -> None:
    client = MagicMock()
    client.invoke_model.return_value = {
        "body": io.BytesIO(
            json.dumps(
                {"content": [{"type": "text", "text": "Start with variables."}]}
            ).encode()
        )
    }
    coach = BedrockAICoach(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        client=client,
    )

    response = coach.generate_response(
        [CoachingMessage(role="user", content="Where should I start?")],
        {"goal": "Learn Python fundamentals"},
    )

    assert response.content == "Start with variables."
    assert response.error is None
    request = client.invoke_model.call_args.kwargs
    assert request["modelId"] == "anthropic.claude-3-haiku-20240307-v1:0"
    assert request["contentType"] == "application/json"
    assert request["accept"] == "application/json"
    assert json.loads(request["body"]) == {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "system": "Deck context: {\"goal\": \"Learn Python fundamentals\"}",
        "messages": [{"role": "user", "content": "Where should I start?"}],
    }


@pytest.mark.parametrize(
    "timeout_error",
    [
        pytest.param(
            ReadTimeoutError(
                endpoint_url="https://bedrock-runtime.us-east-1.amazonaws.com",
                error="The request timed out",
            ),
            id="read-timeout",
        ),
        pytest.param(
            ConnectTimeoutError(
                endpoint_url="https://bedrock-runtime.us-east-1.amazonaws.com",
                error="The connection timed out",
            ),
            id="connect-timeout",
        ),
    ],
)
def test_bedrock_ai_coach_returns_structured_timeout_error(
    timeout_error: BaseException,
) -> None:
    client = MagicMock()
    client.invoke_model.side_effect = timeout_error
    coach = BedrockAICoach(model_id="test-model", client=client)

    response = coach.generate_response([], {})

    assert response.content is None
    assert response.error is not None
    assert response.error.code == "timeout"


def test_bedrock_ai_coach_returns_structured_throttling_error() -> None:
    client = MagicMock()
    client.invoke_model.side_effect = ClientError(
        {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
        "InvokeModel",
    )
    coach = BedrockAICoach(model_id="test-model", client=client)

    response = coach.generate_response([], {})

    assert response.content is None
    assert response.error is not None
    assert response.error.code == "throttled"


def test_bedrock_ai_coach_returns_structured_service_unavailable_error() -> None:
    client = MagicMock()
    client.invoke_model.side_effect = ClientError(
        {"Error": {"Code": "ServiceUnavailableException", "Message": "Unavailable"}},
        "InvokeModel",
    )
    coach = BedrockAICoach(model_id="test-model", client=client)

    response = coach.generate_response([], {})

    assert response.content is None
    assert response.error is not None
    assert response.error.code == "service_unavailable"


def test_dependency_provider_returns_mock_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ai_coach, "settings", replace(settings, use_mock_ai=True))

    coach = ai_coach.get_ai_coach()

    assert isinstance(coach, MockAICoach)