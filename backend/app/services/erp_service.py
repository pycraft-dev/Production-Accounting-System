"""Оркестрация синхронизации с ERP."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.mock_adapter import MockErpAdapter
from app.integrations.onec_http import OneCHttpAdapter
from app.models.erp import ErpEntityLink, ErpSyncRecord


def get_erp_adapter():
    """Возвращает адаптер по настройке ``ERP_ADAPTER``."""

    settings = get_settings()
    if settings.erp_adapter == "mock":
        return MockErpAdapter()
    return OneCHttpAdapter()


async def run_import_catalog(db: Session) -> ErpSyncRecord:
    """
    Импортирует справочник и сохраняет ссылки ``ErpEntityLink``.

    :param db: сессия БД.
    :returns: запись о результате синхронизации.
    """

    adapter = get_erp_adapter()
    rec = ErpSyncRecord(direction="import", success=False, started_at=datetime.now(timezone.utc))
    db.add(rec)
    db.flush()
    try:
        items = await adapter.import_catalog()
        for i, it in enumerate(items):
            ext = str(it.get("external_id", f"mock-{i}"))
            db.add(ErpEntityLink(entity_type="catalog_item", local_id=0, external_id=ext))
        rec.success = True
        rec.message = f"Импортировано позиций: {len(items)}"
    except Exception as e:
        rec.success = False
        rec.message = str(e)
    rec.finished_at = datetime.now(timezone.utc)
    return rec


async def run_export_events(db: Session, payload: dict[str, Any]) -> ErpSyncRecord:
    """Отправляет события во внешнюю систему."""

    adapter = get_erp_adapter()
    rec = ErpSyncRecord(direction="export", success=False, started_at=datetime.now(timezone.utc))
    db.add(rec)
    db.flush()
    try:
        res = await adapter.export_events(payload)
        rec.success = True
        rec.message = str(res)
    except Exception as e:
        rec.success = False
        rec.message = str(e)
    rec.finished_at = datetime.now(timezone.utc)
    return rec
