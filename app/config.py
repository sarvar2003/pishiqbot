from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(alias="BOT_TOKEN")
    database_url: str = Field(alias="DATABASE_URL")
    allowed_telegram_user_id: int = Field(alias="ALLOWED_TELEGRAM_USER_ID")
    timezone: str = Field(default="Asia/Tashkent", alias="TIMEZONE")

    @field_validator("bot_token")
    @classmethod
    def _bot_token_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("BOT_TOKEN must not be empty")
        return v

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("DATABASE_URL must not be empty")
        # Managed Postgres providers (e.g. `fly postgres attach`) hand out a plain
        # postgres:// / postgresql:// URL; we always need the asyncpg driver scheme.
        if v.startswith("postgres://"):
            v = "postgresql+asyncpg://" + v[len("postgres://") :]
        elif v.startswith("postgresql://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://") :]
        return v

    @field_validator("timezone")
    @classmethod
    def _timezone_valid(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unknown TIMEZONE: {v}") from exc
        return v

    @property
    def zone_info(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)


def load_settings() -> Settings:
    """Load and validate settings, raising a clear error at startup on misconfiguration."""
    try:
        return Settings()  # type: ignore[call-arg]
    except Exception as exc:  # noqa: BLE001 - re-raise with a clearer, startup-time message
        raise RuntimeError(
            f"Configuration error: {exc}\n"
            "Check your .env file against .env.example."
        ) from exc


settings = load_settings()
