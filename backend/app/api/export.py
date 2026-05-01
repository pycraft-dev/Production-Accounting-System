"""Экспорт отчётов в Excel и PDF."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response
from sqlalchemy import cast, Date, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.deps import get_current_user
from app.models.defect import Defect
from app.models.user import User
from app.services.export_service import build_defects_excel, build_simple_pdf, build_table_pdf, format_ru_date

router = APIRouter(prefix="/export", tags=["Экспорт"])


@router.get("/defects")
def export_defects(
    fmt: Literal["xlsx", "pdf"],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    date_from: date | None = None,
    date_to: date | None = None,
) -> Response:
    """Экспорт списка брака с фильтрами по дате создания."""

    q = select(Defect).order_by(Defect.created_at.desc()).limit(5000)
    if date_from:
        q = q.where(cast(Defect.created_at, Date) >= date_from)
    if date_to:
        q = q.where(cast(Defect.created_at, Date) <= date_to)
    defects = list(db.scalars(q).all())
    rows = [
        {
            "id": d.id,
            "цех": d.workshop,
            "описание": d.description[:500],
            "статус": d.status.value,
            "приоритет": d.priority.value,
            "категория": d.category.value,
            "создано": format_ru_date(d.created_at),
        }
        for d in defects
    ]
    if fmt == "xlsx":
        blob = build_defects_excel(rows)
        return Response(
            content=blob,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=defects.xlsx"},
        )
    lines = [f"#{r['id']} {r['цех']}: {r['описание'][:200]}" for r in rows[:200]]
    pdf = build_simple_pdf("Экспорт брака", lines)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=defects.pdf"},
    )


@router.get("/analytics-summary.pdf")
def export_analytics_pdf(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Простой PDF-сводка (количество заявок по цехам)."""

    from sqlalchemy import func

    q = select(Defect.workshop, func.count()).group_by(Defect.workshop)
    data = db.execute(q).all()
    headers = ["Цех", "Количество"]
    body = [(str(a[0]), str(a[1])) for a in data]
    pdf = build_table_pdf("Сводка по браку (цеха)", headers, body)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=defects_by_workshop.pdf"},
    )
