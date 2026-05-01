"""Ежедневные отчёты и агрегаты для OEE (ручной ввод)."""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ReportStatus(str, enum.Enum):
    """Статус выполнения ежедневного отчёта."""

    draft = "draft"
    submitted = "submitted"
    verified = "verified"


class DailyReport(Base):
    """
    Ежедневный отчёт сотрудника.

    Поля good_quantity / scrap_quantity и минуты работы используются как fallback
    для расчёта OEE при отсутствии детального журнала оборудования.
    """

    __tablename__ = "daily_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    report_date: Mapped[date] = mapped_column(Date, index=True)
    shift_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tasks_checklist: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), default=ReportStatus.draft)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    planned_work_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_work_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    good_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scrap_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    equipment_id: Mapped[int | None] = mapped_column(ForeignKey("equipment.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
