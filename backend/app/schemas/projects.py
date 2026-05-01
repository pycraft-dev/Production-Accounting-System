"""Схемы проектов."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Создание проекта."""

    name: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    description: str | None = None


class ProjectRead(BaseModel):
    """Проект в ответе."""

    id: int
    name: str
    code: str | None
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
