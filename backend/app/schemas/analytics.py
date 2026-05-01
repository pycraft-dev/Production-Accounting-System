"""Схемы аналитики и экспорта."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class OeeQuery(BaseModel):
    """Параметры расчёта OEE за период."""

    date_from: date
    date_to: date
    equipment_id: int | None = None


class OeeResult(BaseModel):
    """Результат расчёта OEE (доли от 0 до 1)."""

    availability: float
    performance: float
    quality: float
    oee: float
    source_notes: str = Field(description="Откуда взяты данные: детальный журнал и/или отчёты")


class DefectStatsQuery(BaseModel):
    """Фильтры статистики брака."""

    date_from: date | None = None
    date_to: date | None = None


class EmployeeEfficiencyRow(BaseModel):
    """Строка отчёта по сотруднику."""

    user_id: int
    full_name: str
    reports_submitted: int
    defects_created: int
    tasks_completed_ratio: float | None = None
