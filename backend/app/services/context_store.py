"""Persistent deck-context storage behind an injectable S3 seam."""
import json
from typing import Any, Dict, Optional, Protocol, cast

from app.config import settings
from app.models.ai import DeckContext


class S3Client(Protocol):
    def get_object(self, *, Bucket: str, Key: str) -> Dict[str, Any]: ...
    def put_object(self, *, Bucket: str, Key: str, Body: bytes, ContentType: str) -> Any: ...


class ContextStore(Protocol):
    def load(self, user_id: str, deck_id: str) -> DeckContext: ...
    def save(self, user_id: str, deck_id: str, context: DeckContext) -> None: ...


class InMemoryContextStore:
    """A context store suitable for tests and local fakes."""

    def __init__(self) -> None:
        self.values: Dict[str, Dict[str, Any]] = {}

    def load(self, user_id: str, deck_id: str) -> DeckContext:
        return self.values.get(_key(user_id, deck_id), {}).copy()

    def save(self, user_id: str, deck_id: str, context: DeckContext) -> None:
        self.values[_key(user_id, deck_id)] = dict(context)


class S3ContextStore:
    """Store JSON deck context in S3, creating its boto client only when used."""

    def __init__(self, bucket: str, client: Optional[S3Client] = None) -> None:
        self._bucket = bucket
        self._client = client

    def load(self, user_id: str, deck_id: str) -> DeckContext:
        if not self._bucket:
            raise RuntimeError("CONTEXT_BUCKET is not configured")
        try:
            body = self._get_client().get_object(
                Bucket=self._bucket, Key=_key(user_id, deck_id)
            )["Body"].read()
        except Exception as error:
            if _is_missing_object(error):
                return {}
            raise
        value = json.loads(body)
        if not isinstance(value, dict):
            raise ValueError("Deck context must be a JSON object")
        return cast(DeckContext, value)

    def save(self, user_id: str, deck_id: str, context: DeckContext) -> None:
        if not self._bucket:
            raise RuntimeError("CONTEXT_BUCKET is not configured")
        self._get_client().put_object(
            Bucket=self._bucket,
            Key=_key(user_id, deck_id),
            Body=json.dumps(dict(context)).encode(),
            ContentType="application/json",
        )

    def _get_client(self) -> S3Client:
        if self._client is None:
            import boto3
            self._client = cast(S3Client, boto3.client("s3"))
        return self._client


def get_context_store() -> ContextStore:
    """Provide an S3-backed context store for FastAPI dependency injection."""
    return S3ContextStore(settings.context_bucket)


def _key(user_id: str, deck_id: str) -> str:
    return f"{user_id}/{deck_id}/context.json"


def _is_missing_object(error: Exception) -> bool:
    response = getattr(error, "response", {})
    code = response.get("Error", {}).get("Code") if isinstance(response, dict) else None
    return code in {"NoSuchKey", "NoSuchObject", "404"}