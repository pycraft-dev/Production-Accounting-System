"""Абстракция адаптера внешней ERP."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ErpAdapter(Protocol):
    """Контракт клиента ERP (1С HTTP / mock)."""

    async def import_catalog(self) -> list[dict[str, Any]]:
        """Импорт справочников (пример)."""

        ...


    async def export_events(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Экспорт событий (пример)."""

        ...
