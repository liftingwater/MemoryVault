import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Tuple

DEFAULT_ALLOWED_ORIGINS = "http://localhost:5173"


def _get_secrets_from_aws() -> Dict[str, Any]:
    """Load Supabase secrets from AWS Secrets Manager (Lambda runtime only)."""
    secret_arn = os.environ.get("SUPABASE_SECRET_ARN")
    if not secret_arn:
        return {}

    try:
        import boto3

        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_arn)
        return json.loads(response["SecretString"])  # type: ignore[no-any-return]
    except Exception:
        return {}


@lru_cache(maxsize=1)
def _load_secrets() -> Dict[str, str]:
    """Load secrets from environment or AWS Secrets Manager."""
    # First try environment variables (local dev)
    if os.environ.get("SUPABASE_JWT_SECRET"):
        return {
            "service_role_key": os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""),
            "jwt_secret": os.environ.get("SUPABASE_JWT_SECRET", ""),
            "db_url": os.environ.get("SUPABASE_DB_URL", ""),
        }

    # Fall back to AWS Secrets Manager (Lambda runtime)
    return _get_secrets_from_aws()


@dataclass(frozen=True)
class Settings:
    allowed_origins: Tuple[str, ...]
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str
    supabase_db_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        raw = os.environ.get("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS)
        secrets = _load_secrets()

        return cls(
            allowed_origins=tuple(
                origin.strip() for origin in raw.split(",") if origin.strip()
            ),
            supabase_url=os.environ.get("SUPABASE_URL", ""),
            supabase_anon_key=os.environ.get("VITE_SUPABASE_ANON_KEY", ""),
            supabase_service_role_key=secrets.get("service_role_key", ""),
            supabase_jwt_secret=secrets.get("jwt_secret", ""),
            supabase_db_url=secrets.get("db_url", ""),
        )


settings = Settings.from_env()
