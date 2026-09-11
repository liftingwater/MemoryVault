import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Tuple

DEFAULT_ALLOWED_ORIGINS = "http://localhost:5173"


def _get_secrets_from_aws() -> Dict[str, str]:
    """Load Supabase secrets from AWS Secrets Manager (Lambda runtime only)."""
    secret_arn = os.environ.get("SUPABASE_SECRET_ARN")
    if not secret_arn:
        return {}

    try:
        import boto3

        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_arn)
        raw = json.loads(response["SecretString"])
    except Exception:
        return {}

    # scripts/setup-supabase.sh stores the Postgres URL under "connection_string";
    # normalise it to the canonical "db_url" key the rest of the app reads.
    return {
        "db_url": raw.get("db_url") or raw.get("connection_string", ""),
    }


@lru_cache(maxsize=1)
def _load_secrets() -> Dict[str, str]:
    """Load secrets from environment or AWS Secrets Manager."""
    # First try environment variables (local dev)
    if os.environ.get("SUPABASE_DB_URL"):
        return {
            "db_url": os.environ.get("SUPABASE_DB_URL", ""),
        }

    # Fall back to AWS Secrets Manager (Lambda runtime)
    return _get_secrets_from_aws()


@dataclass(frozen=True)
class Settings:
    allowed_origins: Tuple[str, ...]
    supabase_url: str
    supabase_anon_key: str
    supabase_db_url: str
    bedrock_model_id: str
    bedrock_region: str
    use_mock_ai: bool
    context_bucket: str

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
            supabase_db_url=secrets.get("db_url", ""),
            bedrock_model_id=os.environ.get(
                "BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"
            ),
            bedrock_region=os.environ.get(
                "BEDROCK_REGION", os.environ.get("AWS_REGION", "us-east-1")
            ),
            use_mock_ai=os.environ.get("USE_MOCK_AI", "false").lower() == "true",
            context_bucket=os.environ.get("CONTEXT_BUCKET", ""),
        )


settings = Settings.from_env()
