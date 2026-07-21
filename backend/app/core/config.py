"""Configuration via pydantic-settings, loaded from .env file."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_SECRETS_ENV = Path.home() / "agenty" / "secrets" / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", str(_SECRETS_ENV)),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql://appuser:apppassword@localhost:5432/ata_rag_chat"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.5"
    embedding_model: str = "text-embedding-3-small"
    crawl_base_url: str = "https://akademiata.pl"
    basic_auth_user: str = ""
    basic_auth_password: str = ""
    confidence_threshold: float = 0.55
    allowed_origins: str = "http://localhost:3000"


settings = Settings()
