"""Mock-адаптер ERP для разработки и тестов."""

from __future__ import annotations

from typing import Any


class MockErpAdapter:
    """Возвращает фиктивные данные без сетевых вызовов."""

    async def import_catalog(self) -> list[dict[str, Any]]:
        """Имитация импорта номенклатуры."""

        return [
            {"external_id": "ERP-001", "name": "Деталь А", "unit": "шт"},
            {"external_id": "ERP-002", "name": "Деталь Б", "unit": "шт"},
        ]

    async def export_events(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Имитация отправки пакета событий."""

        return {"accepted": True, "count": len(payload.get("items", []))}
