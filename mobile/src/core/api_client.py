"""HTTP-клиент мобильного приложения."""

from __future__ import annotations

import mimetypes
import os
import re
from pathlib import Path
from typing import Any

import requests

from src.core.offline_queue import OfflineQueue


class MobileApiClient:
    """Клиент API с оффлайн-очередью."""

    def __init__(self, base_url: str | None = None, queue_path: str = "offline_queue.db") -> None:
        self.base_url = (base_url or os.environ.get("API_BASE_URL", "http://10.0.2.2:8000")).rstrip("/")
        self.session = requests.Session()
        self.queue = OfflineQueue(queue_path)
        self.access_token: str | None = None
        self.refresh_token: str | None = None

    def login(self, login: str, password: str) -> dict[str, Any]:
        r = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"login": login, "password": password},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token")
        self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
        return data

    def refresh(self) -> None:
        if not self.refresh_token:
            raise RuntimeError("Нет refresh-токена")
        r = self.session.post(
            f"{self.base_url}/api/auth/refresh",
            json={"refresh_token": self.refresh_token},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token", self.refresh_token)
        self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})

    def me(self) -> dict[str, Any]:
        r = self.get("/api/auth/me")
        r.raise_for_status()
        return r.json()

    def post(self, path: str, json_body: dict | None = None, offline_fallback: bool = False) -> requests.Response:
        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        try:
            return self.session.post(url, json=json_body, timeout=60)
        except requests.RequestException:
            if offline_fallback:
                self.queue.enqueue("POST", path, json_body)
            raise

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        """GET-запрос (после входа — с Bearer)."""

        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        timeout = kwargs.pop("timeout", 60)
        return self.session.get(url, timeout=timeout, **kwargs)

    def patch(self, path: str, json_body: dict | None = None) -> requests.Response:
        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        return self.session.patch(url, json=json_body, timeout=60)

    def delete(self, path: str) -> requests.Response:
        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        return self.session.delete(url, timeout=60)

    def change_password(self, current: str, new: str) -> None:
        r = self.session.post(
            f"{self.base_url}/api/auth/change-password",
            json={"current_password": current, "new_password": new},
            timeout=30,
        )
        r.raise_for_status()

    def post_defect_media(self, path: str, file_path: str) -> requests.Response:
        """Загрузка фото/видео к заявке (multipart). path: /api/defects/{id}/photos"""

        mime, _ = mimetypes.guess_type(file_path)
        mime = mime or "application/octet-stream"
        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        with open(file_path, "rb") as f:
            name = Path(file_path).name
            return self.session.post(url, files={"file": (name, f, mime)}, timeout=180)

    def download_file(self, file_id: int) -> tuple[bytes, str | None]:
        """Скачивает ``GET /api/files/{file_id}``. Имя из ``Content-Disposition``, если есть."""

        r = self.get(f"/api/files/{file_id}", timeout=180)
        r.raise_for_status()
        name: str | None = None
        cd = r.headers.get("Content-Disposition") or ""
        m = re.search(r'filename="([^"]+)"', cd)
        if m:
            name = m.group(1)
        return r.content, name

    def sync_queue(self) -> int:
        """Отправляет накопленные POST-запросы. Возвращает число успешных."""

        n = 0
        for item in self.queue.pending():
            try:
                r = self.session.request(item.method, f"{self.base_url}{item.path}", json=item.body, timeout=60)
                if r.ok:
                    self.queue.mark_sent(item.id)
                    n += 1
            except requests.RequestException:
                break
        return n
