"""HTTP-клиент к backend с JWT."""

from __future__ import annotations

from typing import Any

import requests

from src.core.config import get_api_base_url


class ApiClient:
    """Обертка над ``requests.Session`` с авторизацией."""

    def __init__(self) -> None:
        self.base_url = get_api_base_url()
        self.session = requests.Session()
        self.access_token: str | None = None
        self.refresh_token: str | None = None

    def login(self, login: str, password: str) -> dict[str, Any]:
        """Вход: логин (например admin, admin1, worker1)."""

        r = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"login": login, "password": password},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
        return data

    def refresh(self) -> None:
        """Обновляет access по refresh-токену."""

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
        self.refresh_token = data["refresh_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        """Выполняет запрос с одной попыткой refresh при 401."""

        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        timeout = kwargs.pop("timeout", 60)
        r = self.session.request(method, url, timeout=timeout, **kwargs)
        if r.status_code == 401 and self.refresh_token:
            self.refresh()
            r = self.session.request(method, url, timeout=timeout, **kwargs)
        return r

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("DELETE", path, **kwargs)

    def me(self) -> dict[str, Any]:
        """Профиль текущего пользователя."""

        r = self.get("/api/auth/me")
        r.raise_for_status()
        return r.json()

    def change_password(self, current: str, new: str) -> None:
        """Смена пароля текущего пользователя."""

        r = self.session.post(
            f"{self.base_url}/api/auth/change-password",
            json={"current_password": current, "new_password": new},
            timeout=30,
        )
        r.raise_for_status()

    def get_version_info(self) -> dict[str, Any]:
        """``GET /api/version`` (без авторизации)."""

        r = self.session.get(f"{self.base_url}/api/version", timeout=15)
        r.raise_for_status()
        return r.json()
