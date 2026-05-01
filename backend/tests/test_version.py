"""Тесты эндпоинта версии."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_version_endpoint(client: TestClient) -> None:
    """``GET /api/version`` отдаёт структуру с ``api_version``."""

    r = client.get("/api/version")
    assert r.status_code == 200
    body = r.json()
    assert "api_version" in body
    assert "desktop" in body and "mobile" in body
