"""Provider-neutral service interface for MemoryVault's AI coach."""
import json
from typing import Any, Mapping, Optional, Protocol, cast

from botocore.exceptions import ClientError, ConnectTimeoutError, ReadTimeoutError

from app.config import settings
from app.models.ai import (
    AIErrorCode,
    AICoachError,
    CoachingResponse,
    ConversationHistory,
    DeckContext,
)


_BEDROCK_CLIENT_ERROR_RESULTS: Mapping[str, tuple[AIErrorCode, str]] = {
    "ThrottlingException": (
        "throttled",
        "The AI service is busy. Please try again shortly.",
    ),
    "ServiceUnavailableException": (
        "service_unavailable",
        "The AI service is unavailable. Please try again later.",
    ),
}


class BedrockRuntimeClient(Protocol):
    """The portion of the Bedrock Runtime client used by this adapter."""

    def invoke_model(
        self,
        *,
        body: bytes,
        contentType: str,
        accept: str,
        modelId: str,
    ) -> Mapping[str, Any]:
        """Invoke an Amazon Bedrock model."""


class AICoach(Protocol):
    """Generate a coaching response from conversation and deck context."""

    def generate_response(
        self,
        conversation_history: ConversationHistory,
        deck_context: DeckContext,
    ) -> CoachingResponse:
        """Return a response or a structured provider error."""


class MockAICoach:
    """Deterministic AI coach for tests and local development."""

    def __init__(self, canned_response: str = "How can I help with your deck?") -> None:
        self._canned_response = canned_response

    def generate_response(
        self,
        conversation_history: ConversationHistory,
        deck_context: DeckContext,
    ) -> CoachingResponse:
        return CoachingResponse(content=self._canned_response)


class BedrockAICoach:
    """AI coach implementation backed by an Anthropic Claude Bedrock model."""

    def __init__(
        self,
        model_id: str,
        region_name: Optional[str] = None,
        client: Optional[BedrockRuntimeClient] = None,
    ) -> None:
        self._model_id = model_id
        self._client = client or _create_bedrock_client(region_name)

    def generate_response(
        self,
        conversation_history: ConversationHistory,
        deck_context: DeckContext,
    ) -> CoachingResponse:
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "system": f"Deck context: {json.dumps(deck_context)}",
            "messages": [message.model_dump() for message in conversation_history],
        }
        try:
            response = self._client.invoke_model(
                modelId=self._model_id,
                body=json.dumps(request_body).encode(),
                contentType="application/json",
                accept="application/json",
            )
        except (ConnectTimeoutError, ReadTimeoutError):
            return CoachingResponse(
                error=AICoachError(
                    code="timeout",
                    message="The AI service timed out. Please try again.",
                )
            )
        except ClientError as error:
            error_result = _BEDROCK_CLIENT_ERROR_RESULTS.get(
                error.response["Error"]["Code"]
            )
            if error_result:
                code, message = error_result
                return CoachingResponse(
                    error=AICoachError(code=code, message=message)
                )
            raise
        response_body = response["body"].read()
        response_payload = json.loads(response_body)
        text = "".join(
            block["text"]
            for block in response_payload["content"]
            if block["type"] == "text"
        )
        return CoachingResponse(content=text)


def get_ai_coach() -> AICoach:
    """Provide the configured coach for FastAPI dependency injection."""
    if settings.use_mock_ai:
        return MockAICoach()
    return BedrockAICoach(
        model_id=settings.bedrock_model_id,
        region_name=settings.bedrock_region,
    )


def _create_bedrock_client(region_name: Optional[str]) -> BedrockRuntimeClient:
    """Create the runtime client lazily so tests can inject a fake client."""
    import boto3

    return cast(
        BedrockRuntimeClient,
        boto3.client("bedrock-runtime", region_name=region_name),
    )