"""Тесты авторизации."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_register_returns_403(client: TestClient) -> None:
    """Публичная регистрация запрещена."""

    r = client.post("/api/auth/register")
    assert r.status_code == 403


def test_login_and_me(client: TestClient) -> None:
    """Логин выдаёт токен, /me возвращает профиль."""

    r = client.post("/api/auth/login", json={"login": "t@t.com", "password": "password123"})
    assert r.status_code == 200
    body = r.json()
    token = body["access_token"]
    assert body.get("must_change_password") is False
    m = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert m.status_code == 200
    assert m.json()["login"] == "t@t.com"
    assert m.json().get("must_change_password") is False


def test_login_accepts_email_key(client: TestClient) -> None:
    """Поле ``email`` в JSON по-прежнему принимается (алиас для login)."""

    r = client.post("/api/auth/login", json={"email": "t@t.com", "password": "password123"})
    assert r.status_code == 200
