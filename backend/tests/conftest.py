"""Pytest: общие фикстуры."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.database import Base, get_db, reset_engine
from app.main import app
from app.models.user import User, UserRole


@pytest.fixture(scope="function")
def client(monkeypatch: pytest.MonkeyPatch):
    """TestClient с SQLite в памяти и тестовым пользователем."""

    reset_engine()
    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-test-secret-32b")
    get_settings.cache_clear()

    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def _override_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_db
    with SessionLocal() as s:
        s.add(
            User(
                email="t@t.com",
                full_name="Test",
                hashed_password=hash_password("password123"),
                role=UserRole.admin,
                must_change_password=False,
            )
        )
        s.commit()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    reset_engine()
    get_settings.cache_clear()
