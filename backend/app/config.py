import os
from dataclasses import dataclass

DEFAULT_ALLOWED_ORIGINS = "http://localhost:5173"


@dataclass(frozen=True)
class Settings:
    allowed_origins: tuple[str, ...]

    @classmethod
    def from_env(cls) -> "Settings":
        raw = os.environ.get("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS)
        return cls(
            allowed_origins=tuple(
                origin.strip() for origin in raw.split(",") if origin.strip()
            )
        )


settings = Settings.from_env()
