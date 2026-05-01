"""Ежедневные отчёты."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import DEFAULT_PAGE_SIZE
from app.db.database import get_db
from app.deps import get_current_user
from app.models.report import DailyReport
from app.models.user import User
from app.schemas.reports import DailyReportCreate, DailyReportRead, DailyReportUpdate
from app.utils.audit import write_audit

router = APIRouter(prefix="/daily-reports", tags=["Отчёты"])


@router.get("", response_model=list[DailyReportRead])
def list_reports(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = DEFAULT_PAGE_SIZE,
) -> list[DailyReport]:
    """Список отчётов текущего пользователя."""

    q = (
        select(DailyReport)
        .where(DailyReport.user_id == user.id)
        .order_by(DailyReport.report_date.desc())
        .offset(skip)
        .limit(min(limit, 200))
    )
    return list(db.scalars(q).all())


@router.post("", response_model=DailyReportRead, status_code=201)
def create_report(
    payload: DailyReportCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> DailyReport:
    """Создание отчёта."""

    tasks = [t.model_dump() for t in payload.tasks_checklist]
    r = DailyReport(
        user_id=user.id,
        report_date=payload.report_date,
        shift_name=payload.shift_name,
        tasks_checklist=tasks,
        status=payload.status,
        notes=payload.notes,
        planned_work_minutes=payload.planned_work_minutes,
        actual_work_minutes=payload.actual_work_minutes,
        good_quantity=payload.good_quantity,
        scrap_quantity=payload.scrap_quantity,
        equipment_id=payload.equipment_id,
    )
    db.add(r)
    db.flush()
    write_audit(db, user_id=user.id, action="report.create", entity_type="DailyReport", entity_id=r.id)
    db.commit()
    db.refresh(r)
    return r


@router.get("/{report_id}", response_model=DailyReportRead)
def get_report(
    report_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> DailyReport:
    """Отчёт по id."""

    r = db.get(DailyReport, report_id)
    if not r or r.user_id != user.id:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    return r


@router.patch("/{report_id}", response_model=DailyReportRead)
def update_report(
    report_id: int,
    payload: DailyReportUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> DailyReport:
    """Обновление отчёта."""

    r = db.get(DailyReport, report_id)
    if not r or r.user_id != user.id:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    data = payload.model_dump(exclude_unset=True)
    if payload.tasks_checklist is not None:
        r.tasks_checklist = [x.model_dump() for x in payload.tasks_checklist]
    if "shift_name" in data:
        r.shift_name = data["shift_name"]
    if "status" in data and data["status"] is not None:
        r.status = data["status"]
    if "notes" in data:
        r.notes = data["notes"]
    if "planned_work_minutes" in data:
        r.planned_work_minutes = data["planned_work_minutes"]
    if "actual_work_minutes" in data:
        r.actual_work_minutes = data["actual_work_minutes"]
    if "good_quantity" in data:
        r.good_quantity = data["good_quantity"]
    if "scrap_quantity" in data:
        r.scrap_quantity = data["scrap_quantity"]
    if "equipment_id" in data:
        r.equipment_id = data["equipment_id"]
    write_audit(db, user_id=user.id, action="report.update", entity_type="DailyReport", entity_id=r.id, details=data)
    db.commit()
    db.refresh(r)
    return r


@router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Удаление отчёта."""

    r = db.get(DailyReport, report_id)
    if not r or r.user_id != user.id:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    write_audit(db, user_id=user.id, action="report.delete", entity_type="DailyReport", entity_id=r.id)
    db.delete(r)
    db.commit()
    return Response(status_code=204)
