"""Обновление APK: проверка версии и диалог."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests
from kivy.clock import Clock
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog


def _version_tuple(v: str) -> tuple[int, ...]:
    parts: list[int] = []
    for seg in v.strip().split("."):
        if seg.isdigit():
            parts.append(int(seg))
        else:
            break
    return tuple(parts) if parts else (0,)


def _is_newer(remote: str, local: str) -> bool:
    tr, tl = _version_tuple(remote), _version_tuple(local)
    ln = max(len(tr), len(tl))
    tr = tr + (0,) * (ln - len(tr))
    tl = tl + (0,) * (ln - len(tl))
    return tr > tl


def schedule_update_check(app: Any, package_root: Path) -> None:
    """
    После старта UI проверяет ``/api/version``; при более новой версии APK показывает диалог.

    При согласии скачивает файл в каталог данных приложения и сообщает путь.
    """

    def work(_dt: float | int) -> None:
        ver_path = package_root / "version.json"
        if not ver_path.is_file():
            return
        try:
            local_ver = json.loads(ver_path.read_text(encoding="utf-8")).get("version", "0.0.0")
        except (json.JSONDecodeError, OSError):
            return
        base = app.api.base_url.rstrip("/")
        try:
            r = requests.get(f"{base}/api/version", timeout=15)
            r.raise_for_status()
            payload = r.json()
            mob = payload.get("mobile") or {}
            remote_ver = str(mob.get("version", local_ver))
            dl_path = str(mob.get("download_path", "/api/updates/mobile/latest"))
            if not _is_newer(remote_ver, str(local_ver)):
                return
        except (requests.RequestException, ValueError, KeyError):
            return

        dialog = MDDialog(title="Обновление", text=f"Доступна версия {remote_ver} (у вас {local_ver}). Скачать APK?")

        def later(*_a: Any) -> None:
            dialog.dismiss()

        def yes(*_a: Any) -> None:
            dialog.dismiss()
            try:
                url = f"{base}{dl_path}" if dl_path.startswith("/") else f"{base}/{dl_path}"
                dl = requests.get(url, timeout=120)
                if dl.status_code == 404:
                    app.notify("Файл обновления на сервере не настроен")
                    return
                dl.raise_for_status()
                out = Path(app.user_data_dir) / "pas-update.apk"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(dl.content)
                app.notify(f"APK сохранён: {out}. Откройте файл для установки.")
            except requests.RequestException as e:
                app.notify(f"Ошибка загрузки: {e}")

        dialog.buttons = [
            MDFlatButton(text="Позже", on_release=later),
            MDFlatButton(text="Скачать", on_release=yes),
        ]
        dialog.open()

    Clock.schedule_once(work, 1.0)
