"""HTTP-клиент для типового REST/OData сервиса 1С."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings


class OneCHttpAdapter:
    """Минимальный клиент: GET каталога и POST событий (настраиваемые пути)."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def import_catalog(self) -> list[dict[str, Any]]:
        """Загружает JSON со списком позиций (эндпоинт задаётся base_url)."""

        base = self._settings.erp_base_url.rstrip("/")
        headers = {}
        if self._settings.erp_api_token:
            headers["Authorization"] = f"Bearer {self._settings.erp_api_token}"
        async with httpx.AsyncClient(timeout=self._settings.erp_timeout_seconds) as client:
            r = await client.get(f"{base}/catalog", headers=headers)
            r.raise_for_status()
            data = r.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "items" in data:
            return list(data["items"])
        return []

    async def export_events(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Отправляет пакет событий на ERP."""

        base = self._settings.erp_base_url.rstrip("/")
        headers = {"Content-Type": "application/json"}
        if self._settings.erp_api_token:
            headers["Authorization"] = f"Bearer {self._settings.erp_api_token}"
        async with httpx.AsyncClient(timeout=self._settings.erp_timeout_seconds) as client:
            r = await client.post(f"{base}/events", headers=headers, json=payload)
            r.raise_for_status()
            return r.json()
