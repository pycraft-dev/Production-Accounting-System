"""Выдача загруженных файлов (расшифровка при необходимости)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.file import StoredFile
from app.services import file_service

router = APIRouter(prefix="/files", tags=["Файлы"])


@router.get("/{file_id}")
def download_file(
    file_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Скачивание файла по идентификатору метаданных."""

    row = db.get(StoredFile, file_id)
    if not row:
        raise HTTPException(status_code=404, detail="Файл не найден")
    data = file_service.read_file_bytes(row)
    return Response(
        content=data,
        media_type=row.mime_type,
        headers={"Content-Disposition": f'inline; filename="{row.original_filename}"'},
    )
