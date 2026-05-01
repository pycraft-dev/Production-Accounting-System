"""Загрузка настроек из переменных окружения."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация приложения (читается из `.env` и окружения)."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg2://pas_user:pas_secret@localhost:5432/production_accounting"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:8000"
    file_storage_path: str = "./storage/uploads"
    files_encryption_key_base64: str = ""
    log_path: str = "./logs/app.log"
    redis_url: str | None = None
    analytics_cache_ttl_seconds: int = 300
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@example.com"
    smtp_tls: bool = True
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    notify_roles_defect_created: str = "admin,worker,constructor"
    notify_roles_scheme_updated: str = "admin,constructor"
    erp_adapter: Literal["mock", "onec_http"] = "mock"
    erp_base_url: str = "http://localhost:9999/erp"
    erp_api_token: str = ""
    erp_timeout_seconds: float = 30.0
    app_version: str = "1.0.0"
    updates_root: str = "../updates"
    updates_manifest_name: str = "manifest.json"

    @property
    def cors_origins_list(self) -> list[str]:
        """Список разрешённых источников CORS."""

        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @field_validator("files_encryption_key_base64", mode="before")
    @classmethod
    def strip_encryption_key(cls, v: str) -> str:
        """Убирает пробелы у ключа шифрования."""

        if isinstance(v, str):
            return v.strip()
        return str(v) if v else ""


@lru_cache
def get_settings() -> Settings:
    """Возвращает закэшированный экземпляр настроек."""

    return Settings()
