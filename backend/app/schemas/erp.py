"""Схемы ответов ERP."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ErpSyncRead(BaseModel):
    """Результат операции синхронизации."""

    id: int
    direction: str
    success: bool
    message: str | None
    started_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}
