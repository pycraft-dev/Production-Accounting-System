"""Версии схем и согласование."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class ApprovalStatus(str, enum.Enum):
    """Статус согласования чертежа/схемы."""

    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class SchemeChange(Base):
    """Версия схемы (файл + описание изменений конструктора)."""

    __tablename__ = "scheme_changes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer)
    change_description: Mapped[str] = mapped_column(Text)
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus),
        default=ApprovalStatus.draft,
    )
    file_id: Mapped[int] = mapped_column(ForeignKey("stored_files.id"))
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    pdf_annotations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped[Project] = relationship("Project", back_populates="scheme_versions")
    approval_history: Mapped[list["SchemeApprovalHistory"]] = relationship(
        "SchemeApprovalHistory",
        back_populates="scheme_change",
        cascade="all, delete-orphan",
    )


class SchemeApprovalHistory(Base):
    """История изменений статуса согласования."""

    __tablename__ = "scheme_approval_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scheme_change_id: Mapped[int] = mapped_column(ForeignKey("scheme_changes.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    old_status: Mapped[ApprovalStatus | None] = mapped_column(Enum(ApprovalStatus), nullable=True)
    new_status: Mapped[ApprovalStatus] = mapped_column(Enum(ApprovalStatus))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    scheme_change: Mapped["SchemeChange"] = relationship("SchemeChange", back_populates="approval_history")
