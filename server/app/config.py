from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, overridable via environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="LINKFOLIO_", extra="ignore")

    database_url: str = "sqlite:///./linkfolio.db"
    # Dev-only default. Set LINKFOLIO_SECRET_KEY in production.
    secret_key: str = "dev-secret-change-me-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    algorithm: str = "HS256"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
