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
    DeckContextResponse,
    DeckContext,
    GeneratedOutline,
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

    def generate_context(
        self,
        conversation_history: ConversationHistory,
        deck_context: DeckContext,
    ) -> DeckContextResponse:
        """Return a structured update for the persistent deck memory."""


class MockAICoach:
    """Deterministic AI coach for tests and local development."""

    def __init__(
        self,
        canned_response: str = "How can I help with your deck?",
        response: Optional[CoachingResponse] = None,
        generated_outline: Optional[GeneratedOutline] = None,
    ) -> None:
        self._canned_response = canned_response
        self._response = response
        self._generated_outline = generated_outline

    def generate_response(
        self,
        conversation_history: ConversationHistory,
        deck_context: DeckContext,
    ) -> CoachingResponse:
        if self._response is not None:
            return self._response
        return CoachingResponse(
            content=self._canned_response, outline=self._generated_outline
        )

    def generate_context(
        self,
        conversation_history: ConversationHistory,
        deck_context: DeckContext,
    ) -> DeckContextResponse:
        return DeckContextResponse(context=dict(deck_context))


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
            "system": (
                "You are a learning coach. Never write flashcard front or back content. "
                "After the learner has answered questions about their goal, existing "
                "knowledge, and time commitment, begin free-form scope refinement. Do not "
                "offer an outline in that first post-intake reply; you may offer one later. Return "
                "JSON with a required `message` string and optional `outline` object "
                "containing an `items` list of section, title, and optional description. "
                f"Deck context: {json.dumps(deck_context)}"
            ),
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
        return _parse_coaching_response(_extract_text(response))

    def generate_context(
        self,
        conversation_history: ConversationHistory,
        deck_context: DeckContext,
    ) -> DeckContextResponse:
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "system": (
                "Summarize this coaching conversation into persistent deck memory. "
                "Return only a JSON object containing the learner's goals, proficiency, "
                "topics covered, topics to avoid, learning preferences, and card quality "
                "observations when supported by the conversation. Preserve useful existing "
                f"context: {json.dumps(deck_context)}"
            ),
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
            return DeckContextResponse(
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
                return DeckContextResponse(error=AICoachError(code=code, message=message))
            raise
        try:
            context = json.loads(_extract_text(response))
        except (TypeError, ValueError):
            context = None
        if not isinstance(context, dict):
            return DeckContextResponse(
                error=AICoachError(
                    code="service_unavailable",
                    message="The AI service returned an invalid deck context update.",
                )
            )
        return DeckContextResponse(context=context)


def _extract_text(response: Mapping[str, Any]) -> str:
    """Extract concatenated text content from an Anthropic Bedrock response."""
    response_payload = json.loads(response["body"].read())
    return "".join(
        block["text"]
        for block in response_payload["content"]
        if block["type"] == "text"
    )


def _parse_coaching_response(text: str) -> CoachingResponse:
    """Accept the structured coaching envelope while tolerating plain model text."""
    try:
        payload = json.loads(text)
        if not isinstance(payload, dict) or not isinstance(payload.get("message"), str):
            return CoachingResponse(content=text)
        outline = (
            GeneratedOutline.model_validate(payload["outline"])
            if payload.get("outline") is not None
            else None
        )
        return CoachingResponse(content=payload["message"], outline=outline)
    except (TypeError, ValueError):
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