"""Shared field types for API models."""
from typing import Any

from pydantic import BeforeValidator
from typing_extensions import Annotated


def _coerce_uuid_to_str(value: Any) -> Any:
    # Postgres returns uuid columns as uuid.UUID; pydantic v2 will not
    # implicitly coerce that to str, so normalise it here. None is passed
    # through untouched so this type composes with Optional[...] fields.
    return str(value) if value is not None else value


# A str field that accepts a uuid.UUID (or str) input and stores it as str.
UuidStr = Annotated[str, BeforeValidator(_coerce_uuid_to_str)]
