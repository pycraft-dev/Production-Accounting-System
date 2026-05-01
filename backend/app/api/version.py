"""Информация о версии API и пакетах обновления десктопа и мобильного клиента."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import get_settings

router = APIRouter(tags=["Версия и обновления"])


def _manifest_path() -> Path:
    """Абсолютный путь к JSON манифеста обновлений."""

    s = get_settings()
    root = Path(s.updates_root)
    if not root.is_absolute():
        root = (Path.cwd() / root).resolve()
    return root / s.updates_manifest_name


def _load_manifest() -> dict[str, Any]:
    """Читает манифест или возвращает значения по умолчанию."""

    path = _manifest_path()
    if not path.is_file():
        s = get_settings()
        return {
            "min_supported_client": "1.0.0",
            "desktop": {"version": s.app_version, "filename": None},
            "mobile": {"version": s.app_version, "filename": None},
        }
    return json.loads(path.read_text(encoding="utf-8"))


def _updates_dir() -> Path:
    """Корневая папка с артефактами (zip/apk)."""

    return _manifest_path().parent


@router.get("/version")
def get_version() -> JSONResponse:
    """
    Текущая версия API и клиентов, относительные URL скачивания.

    Клиенты сравнивают ``desktop.version`` / ``mobile.version`` с локальным ``version.json``.
    """

    s = get_settings()
    m = _load_manifest()
    payload = {
        "api_version": s.app_version,
        "min_supported_client": m.get("min_supported_client", "1.0.0"),
        "desktop": {
            "version": (m.get("desktop") or {}).get("version", s.app_version),
            "download_path": "/api/updates/desktop/latest",
        },
        "mobile": {
            "version": (m.get("mobile") or {}).get("version", s.app_version),
            "download_path": "/api/updates/mobile/latest",
        },
    }
    return JSONResponse(content=payload)


@router.get("/updates/desktop/latest")
def download_desktop_update() -> FileResponse:
    """Отдаёт архив обновления десктопа (если указан в манифесте)."""

    m = _load_manifest()
    desk = m.get("desktop") or {}
    fn = desk.get("filename")
    if not fn:
        raise HTTPException(status_code=404, detail="Пакет обновления десктопа не настроен")
    path = _updates_dir() / fn
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Файл обновления не найден на сервере")
    return FileResponse(path, filename=path.name, media_type="application/zip")


@router.get("/updates/mobile/latest")
def download_mobile_update() -> FileResponse:
    """Отдаёт APK мобильного клиента (если указан в манифесте)."""

    m = _load_manifest()
    mob = m.get("mobile") or {}
    fn = mob.get("filename")
    if not fn:
        raise HTTPException(status_code=404, detail="APK не настроен в manifest")
    path = _updates_dir() / fn
    if not path.is_file():
        raise HTTPException(status_code=404, detail="APK не найден на сервере")
    return FileResponse(path, filename=path.name, media_type="application/vnd.android.package-archive")
