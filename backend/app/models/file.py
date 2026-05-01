"""Метаданные загруженного файла (хранилище)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class StoredFile(Base):
    """Запись о файле на диске (может быть зашифрован AES-GCM)."""

    __tablename__ = "stored_files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    storage_key: Mapped[str] = mapped_column(String(512), unique=True)
    original_filename: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[str] = mapped_column(String(128))
    size_bytes: Mapped[int] = mapped_column(Integer)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=True)
    uploaded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
