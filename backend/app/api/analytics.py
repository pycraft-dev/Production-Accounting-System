"""Аналитика: OEE, брак, эффективность сотрудников."""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.deps import get_current_user
from app.models.defect import Defect
from app.models.report import DailyReport
from app.models.user import User
from app.schemas.analytics import (
    DefectStatsQuery,
    EmployeeEfficiencyRow,
    OeeQuery,
    OeeResult,
)
from app.services.oee_calculator import collect_oee_inputs, compute_oee_fractions

router = APIRouter(prefix="/analytics", tags=["Аналитика"])


@router.post("/oee", response_model=OeeResult)
def oee_endpoint(
    payload: OeeQuery,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> OeeResult:
    """Расчёт OEE за период."""

    inp = collect_oee_inputs(db, payload.date_from, payload.date_to, payload.equipment_id)
    a, p, q, oee = compute_oee_fractions(inp)
    return OeeResult(availability=a, performance=p, quality=q, oee=oee, source_notes=inp.source_notes)


@router.post("/defects-summary")
def defect_summary(
    payload: DefectStatsQuery,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Сводка по браку: группировка по цеху и категории."""

    q = select(Defect.workshop, Defect.category, func.count()).group_by(Defect.workshop, Defect.category)
    if payload.date_from:
        q = q.where(cast(Defect.created_at, Date) >= payload.date_from)
    if payload.date_to:
        q = q.where(cast(Defect.created_at, Date) <= payload.date_to)
    rows = db.execute(q).all()
    return {
        "rows": [
            {"workshop": r[0], "category": str(r[1]), "count": r[2]}
            for r in rows
        ]
    }


@router.get("/employees", response_model=list[EmployeeEfficiencyRow])
def employee_efficiency(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[EmployeeEfficiencyRow]:
    """Упрощённая эффективность: число отчётов и созданных браков."""

    users = list(db.scalars(select(User)).all())
    out: list[EmployeeEfficiencyRow] = []
    for u in users:
        rq = select(func.count()).select_from(DailyReport).where(DailyReport.user_id == u.id)
        dq = select(func.count()).select_from(Defect).where(Defect.created_by_id == u.id)
        if date_from:
            t_from = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
            rq = rq.where(DailyReport.report_date >= date_from)
            dq = dq.where(Defect.created_at >= t_from)
        if date_to:
            t_to = datetime.combine(date_to, time.max, tzinfo=timezone.utc)
            rq = rq.where(DailyReport.report_date <= date_to)
            dq = dq.where(Defect.created_at <= t_to)
        reports_submitted = int(db.scalar(rq) or 0)
        defects_created = int(db.scalar(dq) or 0)
        out.append(
            EmployeeEfficiencyRow(
                user_id=u.id,
                full_name=u.full_name,
                reports_submitted=reports_submitted,
                defects_created=defects_created,
                tasks_completed_ratio=None,
            )
        )
    return out
