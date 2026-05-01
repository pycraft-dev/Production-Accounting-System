"""Схемы версий схем."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.scheme import ApprovalStatus


class SchemeChangeCreate(BaseModel):
    """Метаданные новой версии (файл загружается отдельно)."""

    change_description: str = Field(min_length=1)
    approval_status: ApprovalStatus = ApprovalStatus.draft


class SchemeChangeUpdate(BaseModel):
    """Обновление версии схемы."""

    change_description: str | None = None
    approval_status: ApprovalStatus | None = None


class SchemeApprovalNote(BaseModel):
    """Заметка при смене статуса согласования."""

    new_status: ApprovalStatus
    note: str | None = None


class SchemeChangeRead(BaseModel):
    """Версия схемы в ответе."""

    id: int
    project_id: int
    version: int
    change_description: str
    approval_status: ApprovalStatus
    file_id: int
    created_by_id: int
    pdf_annotations: list[dict[str, Any]] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class PdfAnnotationCreate(BaseModel):
    """Аннотация к странице PDF (хранится отдельно от бинарника)."""

    page: int = Field(ge=0)
    x: float
    y: float
    text: str = Field(min_length=1)
