from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_SECRET_KEY = "dev-secret-change-me-in-production"


class Settings(BaseSettings):
    """Runtime configuration, overridable via environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="LINKFOLIO_", extra="ignore")

    database_url: str = "sqlite:///./linkfolio.db"
    # "dev" and "test" may use the built-in secret key; any other value
    # (e.g. "production") refuses to start with a missing/default key.
    env: str = "dev"
    # Dev-only default. Set LINKFOLIO_SECRET_KEY in production.
    secret_key: str = DEFAULT_SECRET_KEY
    rate_limit_enabled: bool = True
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    algorithm: str = "HS256"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @model_validator(mode="after")
    def _require_real_secret_outside_dev(self) -> "Settings":
        if self.env.lower() not in ("dev", "test") and self.secret_key in ("", DEFAULT_SECRET_KEY):
            raise ValueError(
                "LINKFOLIO_SECRET_KEY must be set to a non-default value when LINKFOLIO_ENV "
                f"is {self.env!r}"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
