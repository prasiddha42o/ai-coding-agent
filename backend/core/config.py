"""Application configuration, sourced from environment variables / .env."""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    debug: bool = True

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ai_coding_agent"

    # Auth
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    # LLM provider
    llm_provider: Literal["anthropic", "openai", "mock"] = "anthropic"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5"
    openai_api_key: str | None = None

    # Repository storage
    workspaces_dir: str = "backend/workspaces"
    uploads_dir: str = "backend/uploads"
    max_upload_size_mb: int = 200

    # Background execution
    command_timeout_seconds: int = 120


@lru_cache
def get_settings() -> Settings:
    return Settings()
