"""Схемы брака."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.defect import DefectCategory, DefectPriority, DefectStatus
from app.constants import DEFECT_WORKSHOP_CHOICES


class DefectCreate(BaseModel):
    """Создание заявки по браку."""

    description: str = Field(min_length=1)
    workshop: str = Field(min_length=1, max_length=255)
    priority: DefectPriority = DefectPriority.medium
    category: DefectCategory = DefectCategory.production
    part_number: str | None = Field(default=None, max_length=128)
    machine: str | None = Field(default=None, max_length=255)
    project_id: int | None = None
    assignee_id: int | None = None

    @field_validator("workshop")
    @classmethod
    def workshop_must_be_allowed(cls, v: str) -> str:
        if v not in DEFECT_WORKSHOP_CHOICES:
            raise ValueError(
                f"Цех должен быть одним из: {', '.join(DEFECT_WORKSHOP_CHOICES)}",
            )
        return v


class DefectUpdate(BaseModel):
    """Обновление заявки."""

    description: str | None = None
    workshop: str | None = Field(default=None, max_length=255)
    status: DefectStatus | None = None
    priority: DefectPriority | None = None
    category: DefectCategory | None = None
    part_number: str | None = Field(default=None, max_length=128)
    machine: str | None = Field(default=None, max_length=255)
    project_id: int | None = None
    assignee_id: int | None = None

    @field_validator("workshop")
    @classmethod
    def workshop_must_be_allowed(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in DEFECT_WORKSHOP_CHOICES:
            raise ValueError(
                f"Цех должен быть одним из: {', '.join(DEFECT_WORKSHOP_CHOICES)}",
            )
        return v


class DefectCommentCreate(BaseModel):
    """Новый комментарий."""

    body: str = Field(min_length=1)


class DefectCommentRead(BaseModel):
    """Комментарий в ответе."""

    id: int
    user_id: int
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class StoredFileRef(BaseModel):
    """Краткая ссылка на файл."""

    id: int
    original_filename: str
    mime_type: str

    model_config = {"from_attributes": True}


class DefectRead(BaseModel):
    """Заявка по браку."""

    id: int
    description: str
    workshop: str
    status: DefectStatus
    priority: DefectPriority
    category: DefectCategory
    part_number: str | None
    machine: str | None
    project_id: int | None
    created_by_id: int
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DefectReadDetail(DefectRead):
    """Заявка с вложениями (IDs файлов подставляются отдельно в роутере при необходимости)."""

    attachment_file_ids: list[int] = []
