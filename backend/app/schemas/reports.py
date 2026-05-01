"""Схемы ежедневных отчётов."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.report import ReportStatus


class ChecklistItem(BaseModel):
    """Пункт чек-листа."""

    text: str
    done: bool = False


class DailyReportCreate(BaseModel):
    """Создание отчёта."""

    report_date: date
    shift_name: str | None = Field(default=None, max_length=128)
    tasks_checklist: list[ChecklistItem] = []
    status: ReportStatus = ReportStatus.draft
    notes: str | None = None
    planned_work_minutes: float | None = None
    actual_work_minutes: float | None = None
    good_quantity: int | None = Field(default=None, ge=0)
    scrap_quantity: int | None = Field(default=None, ge=0)
    equipment_id: int | None = None


class DailyReportUpdate(BaseModel):
    """Обновление отчёта."""

    shift_name: str | None = Field(default=None, max_length=128)
    tasks_checklist: list[ChecklistItem] | None = None
    status: ReportStatus | None = None
    notes: str | None = None
    planned_work_minutes: float | None = None
    actual_work_minutes: float | None = None
    good_quantity: int | None = Field(default=None, ge=0)
    scrap_quantity: int | None = Field(default=None, ge=0)
    equipment_id: int | None = None


class DailyReportRead(BaseModel):
    """Отчёт в ответе."""

    id: int
    user_id: int
    report_date: date
    shift_name: str | None
    tasks_checklist: list[dict[str, Any]]
    status: ReportStatus
    notes: str | None
    planned_work_minutes: float | None
    actual_work_minutes: float | None
    good_quantity: int | None
    scrap_quantity: int | None
    equipment_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
