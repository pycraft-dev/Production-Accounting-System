"""Связи с внешней ERP и журнал синхронизаций."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ErpEntityLink(Base):
    """Сопоставление локальной сущности с идентификатором во внешней системе."""

    __tablename__ = "erp_entity_links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    local_id: Mapped[int] = mapped_column(Integer, index=True)
    external_id: Mapped[str] = mapped_column(String(128), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ErpSyncRecord(Base):
    """Результат последних запусков синхронизации с ERP."""

    __tablename__ = "erp_sync_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    direction: Mapped[str] = mapped_column(String(32))
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
