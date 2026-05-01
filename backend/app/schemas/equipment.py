"""Схемы оборудования и простоев."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class EquipmentCreate(BaseModel):
    """Создание записи оборудования."""

    name: str = Field(min_length=1, max_length=255)
    workshop: str = Field(min_length=1, max_length=255)
    ideal_cycle_seconds: float | None = Field(default=None, gt=0)
    is_active: bool = True


class EquipmentUpdate(BaseModel):
    """Обновление оборудования."""

    name: str | None = Field(default=None, max_length=255)
    workshop: str | None = Field(default=None, max_length=255)
    ideal_cycle_seconds: float | None = Field(default=None, gt=0)
    is_active: bool | None = None


class EquipmentRead(BaseModel):
    """Оборудование в ответе."""

    id: int
    name: str
    workshop: str
    ideal_cycle_seconds: float | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DowntimeCreate(BaseModel):
    """Регистрация простоя."""

    equipment_id: int
    started_at: datetime
    ended_at: datetime
    reason_code: str = Field(min_length=1, max_length=64)
    note: str | None = None


class DowntimeUpdate(BaseModel):
    """Изменение записи простоя."""

    started_at: datetime | None = None
    ended_at: datetime | None = None
    reason_code: str | None = Field(default=None, max_length=64)
    note: str | None = None


class DowntimeRead(BaseModel):
    """Простой в ответе."""

    id: int
    equipment_id: int
    started_at: datetime
    ended_at: datetime
    reason_code: str
    note: str | None
    created_by_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
