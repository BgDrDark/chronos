import json
import os
import secrets
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet
from pydantic import computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the directory where config.py is located
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"


def _ensure_env_key(key_name: str, value: str | None = None, generate: bool = True, key_type: str = "hex") -> str | None:
    """Ensures a key exists in .env file.
    If value is None and generate=True, generates and saves a new key.
    
    Args:
        key_name: Name of the environment variable
        value: Optional existing value
        generate: Whether to generate if not found
        key_type: "hex" for regular secrets, "fernet" for Fernet keys
    Returns:
        The key value

    """
    if value:
        return value

    # Try to read from .env file directly
    if env_path.exists():
        with open(env_path) as f:
            content = f.read()
            for line in content.split("\n"):
                if line.startswith(f"{key_name}=") and not line.strip().startswith("#"):
                    return line.split("=", 1)[1].strip()

    # Generate new key if not found
    if generate:
        if key_type == "fernet":
            new_value = Fernet.generate_key().decode()
        else:
            new_value = secrets.token_hex(32)

        # Append to .env file
        with open(env_path, "a") as f:
            f.write(f"\n# Auto-generated {key_name}\n{key_name}={new_value}\n")
        print(f"Auto-generated {key_name} and saved to .env")
        return new_value

    return None

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=env_path, env_file_encoding="utf-8", extra="ignore")
    DEBUG: bool = False
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "chronosdb"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    # Chronos-specific overrides for backward compatibility
    CHRONOS_DB_USER: str | None = None
    CHRONOS_DB_PASSWORD: str | None = None
    CHRONOS_DB_NAME: str | None = None
    CHRONOS_DB_HOST: str | None = None
    CHRONOS_DB_PORT: int | None = None

    # Secrets - will be loaded from environment if set, otherwise from .env file
    JWT_SECRET_KEY: str | None = None
    ENCRYPTION_KEY: str | None = None
    CSRF_SECRET_KEY: str | None = None
    DEPLOY_API_KEY: str | None = None

    # Application Version
    VERSION: str = "unknown"

    @computed_field
    @property
    def database_url_computed(self) -> str:
        user = self.CHRONOS_DB_USER or self.POSTGRES_USER
        password = self.CHRONOS_DB_PASSWORD or self.POSTGRES_PASSWORD
        db = self.CHRONOS_DB_NAME or self.POSTGRES_DB
        host = self.CHRONOS_DB_HOST or self.POSTGRES_HOST
        port = self.CHRONOS_DB_PORT or self.POSTGRES_PORT
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    # Legacy alias for DATABASE_URL
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return self.database_url_computed

    @model_validator(mode="after")
    def ensure_secrets(self) -> "Settings":
        """Ensure all secrets are present, generating them if necessary."""
        if not self.JWT_SECRET_KEY:
            self.JWT_SECRET_KEY = _ensure_env_key("JWT_SECRET_KEY")
        if not self.ENCRYPTION_KEY:
            self.ENCRYPTION_KEY = _ensure_env_key("ENCRYPTION_KEY", key_type="fernet")
        if not self.CSRF_SECRET_KEY:
            self.CSRF_SECRET_KEY = _ensure_env_key("CSRF_SECRET_KEY")
        return self

    def get_deploy_key(self) -> str:
        """Get deploy/update API key with file fallback and auto-rotation support."""
        # 1. Env var (highest priority)
        key = os.environ.get("DEPLOY_API_KEY")
        if key:
            return key.strip()

        # 2. Shared file (production - path from env var)
        key_file = os.environ.get("UPDATE_KEY_FILE", "/project/scripts/update.key")
        if os.path.exists(key_file):
            with open(key_file) as f:
                return f.read().strip()

        # 3. Fallback: generate temporary key
        new_key = secrets.token_hex(32)
        import logging
        logging.getLogger(__name__).warning(
            f"DEPLOY_API_KEY not configured and no update.key found at {key_file}. "
            f"Generated temporary key: {new_key[:8]}...",
        )
        return new_key

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    COOKIE_SECURE: bool = True  # Set to False for HTTP development
    AUTH_KEY_ROTATION_DAYS: int = 30
    AUTH_KEY_RETENTION_DAYS: int = 90
    BACKEND_CORS_ORIGINS: list[str] | str = []
    TIMEZONE: str = "Europe/Sofia"

    # SMTP Fallback Settings (used only if DB GlobalSettings are missing)
    MAIL_SERVER: str | None = None
    MAIL_PORT: int = 587
    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None
    MAIL_FROM: str | None = None
    MAIL_FROM_NAME: str = "Chronos Working Time"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    FRONTEND_URL: str = "http://localhost:5173"
    API_URL: str = "http://localhost:8000"
    # QR Code Settings
    QR_TOKEN_REGEN_MINUTES: int = 15

    # Session Settings
    SESSION_MAX_AGE_HOURS: int = 12

    # Google Calendar Integration
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None
    GOOGLE_CALENDAR_WEBHOOK_SECRET: str | None = None
    GOOGLE_SYNC_ENABLED: bool = True
    GOOGLE_SYNC_BATCH_SIZE: int = 50
    GOOGLE_SYNC_RETRY_ATTEMPTS: int = 3
    GOOGLE_SYNC_TIMEOUT_SECONDS: int = 30

    @model_validator(mode="after")
    def set_derived_urls(self) -> "Settings":
        if not self.GOOGLE_REDIRECT_URI:
            self.GOOGLE_REDIRECT_URI = f"{self.FRONTEND_URL}/auth/google/callback"
        return self

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, str) and v.startswith("["):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Fallback for Python-style lists with single quotes
                return [i.strip().strip("'\"") for i in v.strip("[]").split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)


settings = Settings()
