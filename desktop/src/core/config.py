"""Настройки десктоп-клиента."""

from __future__ import annotations

import os


def get_api_base_url() -> str:
    """Базовый URL API (переменная окружения ``API_BASE_URL``)."""

    return os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
