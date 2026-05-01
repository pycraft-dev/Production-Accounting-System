"""Брак: заявки, вложения, комментарии, история статусов."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class DefectStatus(str, enum.Enum):
    """Статус заявки по браку."""

    new = "new"
    in_progress = "in_progress"
    resolved = "resolved"
    rejected = "rejected"


class DefectPriority(str, enum.Enum):
    """Приоритет брака."""

    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class DefectCategory(str, enum.Enum):
    """Категория брака."""

    production = "production"
    material = "material"
    equipment = "equipment"


class Defect(Base):
    """Заявка учёта брака."""

    __tablename__ = "defects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    description: Mapped[str] = mapped_column(Text)
    workshop: Mapped[str] = mapped_column(String(255))
    status: Mapped[DefectStatus] = mapped_column(Enum(DefectStatus), default=DefectStatus.new)
    priority: Mapped[DefectPriority] = mapped_column(Enum(DefectPriority), default=DefectPriority.medium)
    category: Mapped[DefectCategory] = mapped_column(Enum(DefectCategory), default=DefectCategory.production)
    part_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    machine: Mapped[str | None] = mapped_column(String(255), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    creator: Mapped[User] = relationship("User", foreign_keys=[created_by_id], back_populates="defects_created")
    attachments: Mapped[list["DefectAttachment"]] = relationship(
        "DefectAttachment",
        back_populates="defect",
        cascade="all, delete-orphan",
    )
    comments: Mapped[list["DefectComment"]] = relationship(
        "DefectComment",
        back_populates="defect",
        cascade="all, delete-orphan",
    )
    status_history: Mapped[list["DefectStatusHistory"]] = relationship(
        "DefectStatusHistory",
        back_populates="defect",
        cascade="all, delete-orphan",
    )


class DefectAttachment(Base):
    """Вложение (фото) к заявке по браку."""

    __tablename__ = "defect_attachments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    defect_id: Mapped[int] = mapped_column(ForeignKey("defects.id", ondelete="CASCADE"))
    file_id: Mapped[int] = mapped_column(ForeignKey("stored_files.id"))
    kind: Mapped[str] = mapped_column(String(32), default="photo")

    defect: Mapped["Defect"] = relationship("Defect", back_populates="attachments")


class DefectComment(Base):
    """Комментарий к заявке по браку."""

    __tablename__ = "defect_comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    defect_id: Mapped[int] = mapped_column(ForeignKey("defects.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    defect: Mapped["Defect"] = relationship("Defect", back_populates="comments")


class DefectStatusHistory(Base):
    """История смены статуса брака."""

    __tablename__ = "defect_status_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    defect_id: Mapped[int] = mapped_column(ForeignKey("defects.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    old_status: Mapped[DefectStatus | None] = mapped_column(Enum(DefectStatus), nullable=True)
    new_status: Mapped[DefectStatus] = mapped_column(Enum(DefectStatus))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    defect: Mapped["Defect"] = relationship("Defect", back_populates="status_history")
