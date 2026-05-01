"""Локальное сохранение сессии (как на десктопе: refresh-токен, логин, без пароля)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.core.api_client import MobileApiClient


def _path(root: Path) -> Path:
    d = root / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d / "session.json"


def load(root: Path) -> dict[str, Any] | None:
    p = _path(root)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def load_last_login(root: Path) -> str:
    data = load(root)
    if not data:
        return ""
    return str(data.get("last_login", ""))


def save_session(root: Path, client: MobileApiClient, last_login: str) -> None:
    p = _path(root)
    payload = {
        "last_login": last_login.strip(),
        "base_url": client.base_url.rstrip("/"),
        "refresh_token": client.refresh_token or "",
        "access_token": client.access_token or "",
    }
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def clear(root: Path) -> None:
    p = _path(root)
    p.unlink(missing_ok=True)


def invalidate_tokens(root: Path) -> None:
    data = load(root)
    if not data:
        return
    data.pop("refresh_token", None)
    data.pop("access_token", None)
    p = _path(root)
    try:
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def try_restore_session(root: Path, client: MobileApiClient) -> tuple[bool, dict[str, Any] | None]:
    """
    Восстанавливает сессию при совпадении base_url: refresh, затем /me.
    """

    data = load(root)
    if not data:
        return False, None
    stored_url = str(data.get("base_url", "")).rstrip("/")
    current_url = client.base_url.rstrip("/")
    if stored_url != current_url:
        invalidate_tokens(root)
        return False, None
    rt = data.get("refresh_token")
    if not rt:
        return False, None
    client.refresh_token = str(rt)
    at = data.get("access_token")
    client.access_token = str(at) if at else None
    if client.access_token:
        client.session.headers.update({"Authorization": f"Bearer {client.access_token}"})
    try:
        client.refresh()
    except Exception:
        invalidate_tokens(root)
        return False, None
    try:
        prof = client.me()
    except Exception:
        invalidate_tokens(root)
        return False, None
    save_session(root, client, str(data.get("last_login", "")))
    return True, prof
