"""Проверка и применение обновления десктоп-клиента с сервера."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import requests

from src.core.config import get_api_base_url


def _version_tuple(v: str) -> tuple[int, ...]:
    """Сравнимая версия ``1.2.3`` → ``(1, 2, 3)``."""

    parts: list[int] = []
    for seg in v.strip().split("."):
        if seg.isdigit():
            parts.append(int(seg))
        else:
            break
    return tuple(parts) if parts else (0,)


def _is_newer(remote: str, local: str) -> bool:
    """True, если ``remote`` строго новее ``local``."""

    tr, tl = _version_tuple(remote), _version_tuple(local)
    ln = max(len(tr), len(tl))
    tr = tr + (0,) * (ln - len(tr))
    tl = tl + (0,) * (ln - len(tl))
    return tr > tl


def check_and_apply_updates(app_root: Path) -> None:
    """
    При старте: если на сервере новее ``version.json``, скачивает zip и распаковывает в каталог приложения.

    После успеха перезапускает процесс (``os.execv``). Ошибки сети игнорируются (работа без сервера).
    """

    ver_file = app_root / "version.json"
    if not ver_file.is_file():
        return
    try:
        local_ver = json.loads(ver_file.read_text(encoding="utf-8")).get("version", "0.0.0")
    except (json.JSONDecodeError, OSError):
        return
    base = get_api_base_url().rstrip("/")
    try:
        r = requests.get(f"{base}/api/version", timeout=15)
        r.raise_for_status()
        payload = r.json()
        remote_ver = (payload.get("desktop") or {}).get("version", local_ver)
        path_rel = (payload.get("desktop") or {}).get("download_path", "/api/updates/desktop/latest")
        if not _is_newer(str(remote_ver), str(local_ver)):
            return
        dl = requests.get(f"{base}{path_rel}", timeout=120)
        if dl.status_code == 404:
            return
        dl.raise_for_status()
    except (requests.RequestException, ValueError, KeyError):
        return

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(dl.content)
        tmp_path = Path(tmp.name)
    try:
        with zipfile.ZipFile(tmp_path, "r") as zf:
            zf.extractall(app_root)
        ver_file.write_text(
            json.dumps({"version": str(remote_ver), "channel": "desktop"}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    exe = sys.executable
    script = str(Path(sys.argv[0]).resolve())
    os.execv(exe, [exe, script, *sys.argv[1:]])
