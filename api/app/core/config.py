from typing import Annotated, Literal
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore",
    )

    # === アプリ環境設定 ===
    APP_ENV: Literal["dev", "production", "test"] = "dev"
    LOG_LEVEL: str = "INFO"
    ENABLE_SIGNUP: bool = True
    AUTH_LOGIN_ID_MODE: Literal["email", "login_id"] = "email"
    FRONTEND_ORIGINS: Annotated[list[str], NoDecode] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # === Database設定 ===
    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@db:5432/project_db?sslmode=disable"
    )

    # === 認証関連設定 ===
    ACCESS_TOKEN_SECRET: str = "randomstring"
    ACCESS_TOKEN_EXPIRES_SECONDS: int = 900
    REFRESH_TOKEN_SECRET: str = "randomstring"
    REFRESH_TOKEN_EXPIRES_SECONDS: int = 2592000
    REFRESH_TOKEN_REMEMBER_ME_EXPIRES_SECONDS: int = 2592000

    # === パスワード再設定 ===
    PASSWORD_RESET_URL_BASE: str = "http://localhost:3000/reset-password"
    PASSWORD_RESET_TOKEN_EXPIRES_MINUTES: int = 30
    PASSWORD_RESET_RESEND_INTERVAL_MINUTES: int = 5

    # === Mail ===
    MAIL_PROVIDER: Literal["mailhog", "smtp"] = "mailhog"
    MAIL_FROM: str = "no-reply@example.local"
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True

    @field_validator("APP_ENV", "AUTH_LOGIN_ID_MODE", "MAIL_PROVIDER", mode="before")
    @classmethod
    def normalize_choices(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("FRONTEND_ORIGINS", mode="before")
    @classmethod
    def parse_frontend_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return [origin.strip() for origin in value if origin.strip()]

    @field_validator("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: str | None) -> str | None:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.APP_ENV == "production":
            self._validate_production_secret("ACCESS_TOKEN_SECRET")
            self._validate_production_secret("REFRESH_TOKEN_SECRET")
            self._validate_production_frontend_origins()

        if self.MAIL_PROVIDER == "smtp" and not self.SMTP_HOST:
            raise ValueError("SMTP_HOST is required when MAIL_PROVIDER=smtp")

        return self

    def _validate_production_secret(self, name: str) -> None:
        value = getattr(self, name)
        if value == "randomstring" or value.startswith("change-me"):
            raise ValueError(f"{name} must be changed for production")
        if not value.strip():
            raise ValueError(f"{name} must not be empty for production")

    def _validate_production_frontend_origins(self) -> None:
        for origin in self.FRONTEND_ORIGINS:
            hostname = urlparse(origin).hostname
            if origin == "*" or hostname in {"localhost", "127.0.0.1", "::1"}:
                raise ValueError("FRONTEND_ORIGINS contains local origin in production")


config = Config()
