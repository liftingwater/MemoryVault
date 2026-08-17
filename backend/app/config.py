import os
from dataclasses import dataclass

DEFAULT_ALLOWED_ORIGINS = "http://localhost:5173"


@dataclass(frozen=True)
class Settings:
    allowed_origins: tuple[str, ...]
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str
    supabase_db_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        raw = os.environ.get("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS)
        return cls(
            allowed_origins=tuple(
                origin.strip() for origin in raw.split(",") if origin.strip()
            ),
            supabase_url=os.environ.get("SUPABASE_URL", ""),
            supabase_anon_key=os.environ.get("VITE_SUPABASE_ANON_KEY", ""),
            supabase_service_role_key=os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""),
            supabase_jwt_secret=os.environ.get("SUPABASE_JWT_SECRET", ""),
            supabase_db_url=os.environ.get("SUPABASE_DB_URL", ""),
        )


settings = Settings.from_env()
