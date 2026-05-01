"""Синхронизация с ERP (admin)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.deps import require_role
from app.models.erp import ErpSyncRecord
from app.models.user import User, UserRole
from app.schemas.erp import ErpSyncRead
from app.services import erp_service
from app.utils.audit import write_audit

router = APIRouter(prefix="/erp", tags=["ERP"])


class ExportPayload(BaseModel):
    """Тело запроса экспорта событий."""

    items: list[dict[str, Any]] = []


@router.post("/import", response_model=ErpSyncRead)
async def erp_import(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.admin))],
) -> ErpSyncRecord:
    """Запуск импорта справочников из ERP."""

    rec = await erp_service.run_import_catalog(db)
    write_audit(db, user_id=user.id, action="erp.import", entity_type="ErpSync", entity_id=rec.id)
    db.commit()
    db.refresh(rec)
    return rec


@router.post("/export", response_model=ErpSyncRead)
async def erp_export(
    payload: ExportPayload,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.admin))],
) -> ErpSyncRecord:
    """Отправка пакета событий во внешнюю систему."""

    rec = await erp_service.run_export_events(db, {"items": payload.items})
    write_audit(db, user_id=user.id, action="erp.export", entity_type="ErpSync", entity_id=rec.id)
    db.commit()
    db.refresh(rec)
    return rec


@router.get("/status", response_model=list[dict])
def erp_status(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.admin))],
    limit: int = 20,
) -> list[ErpSyncRecord]:
    """Последние записи синхронизации."""

    rows = list(
        db.scalars(
            select(ErpSyncRecord).order_by(ErpSyncRecord.started_at.desc()).limit(min(limit, 100))
        ).all()
    )
    return [
        {
            "id": r.id,
            "direction": r.direction,
            "success": r.success,
            "message": r.message,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        }
        for r in rows
    ]
