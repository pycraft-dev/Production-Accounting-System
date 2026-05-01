"""Сохранение загружаемых файлов с опциональным шифрованием AES-GCM."""

from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.crypto import decrypt_file_bytes, encrypt_file_bytes
from app.models.file import StoredFile

logger = logging.getLogger(__name__)


def _safe_fragment(name: str) -> str:
    """Убирает опасные символы из имени файла для суффикса."""

    base = Path(name).name
    return re.sub(r"[^a-zA-Z0-9._-]", "_", base)[:120] or "file"


def save_uploaded_file(
    db: Session,
    *,
    content: bytes,
    original_filename: str,
    mime_type: str,
    uploaded_by_id: int | None,
) -> StoredFile:
    """
    Сохраняет байты на диск и создаёт запись ``StoredFile``.

    Если в настройках задан ключ ``FILES_ENCRYPTION_KEY_BASE64``, содержимое
    шифруется. Иначе в лог пишется предупреждение и файл хранится как есть.

    :param db: сессия БД.
    :param content: содержимое файла.
    :param original_filename: исходное имя.
    :param mime_type: MIME-тип.
    :param uploaded_by_id: кто загрузил.
    :returns: ORM-объект с присвоенным id.
    """

    settings = get_settings()
    root = Path(settings.file_storage_path)
    root.mkdir(parents=True, exist_ok=True)
    key_b64 = settings.files_encryption_key_base64
    uid = uuid.uuid4().hex
    if key_b64:
        blob = encrypt_file_bytes(content, key_b64)
        storage_key = f"{uid}.enc"
        is_encrypted = True
    else:
        logger.warning("Ключ шифрования файлов не задан — сохраняем без AES-GCM")
        blob = content
        storage_key = f"{uid}_{_safe_fragment(original_filename)}"
        is_encrypted = False
    path = root / storage_key
    path.write_bytes(blob)
    row = StoredFile(
        storage_key=storage_key,
        original_filename=original_filename,
        mime_type=mime_type,
        size_bytes=len(content),
        is_encrypted=is_encrypted,
        uploaded_by_id=uploaded_by_id,
    )
    db.add(row)
    db.flush()
    return row


def read_file_bytes(stored: StoredFile) -> bytes:
    """
    Читает файл с диска и при необходимости расшифровывает.

    :param stored: ORM-объект метаданных.
    :returns: исходные байты файла.
    """

    settings = get_settings()
    path = Path(settings.file_storage_path) / stored.storage_key
    raw = path.read_bytes()
    if stored.is_encrypted:
        key = settings.files_encryption_key_base64
        if not key:
            raise RuntimeError("Файл зашифрован, но ключ не задан в окружении")
        return decrypt_file_bytes(raw, key)
    return raw


ALLOWED_DEFECT_MEDIA_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "video/mp4",
        "video/quicktime",
        "video/webm",
    }
)

# обратная совместимость имён
ALLOWED_DEFECT_PHOTO_TYPES = ALLOWED_DEFECT_MEDIA_TYPES
ALLOWED_SCHEME_TYPES = {"application/pdf", "image/png", "image/jpeg"}
