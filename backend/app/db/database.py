"""Подключение к БД и фабрика сессий."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Базовый класс моделей SQLAlchemy 2.0."""

    pass


_engine_singleton = None
_SessionLocal = None


def reset_engine() -> None:
    """Сбрасывает singleton движка (для тестов)."""

    global _engine_singleton, _SessionLocal
    if _engine_singleton is not None:
        _engine_singleton.dispose()
    _engine_singleton = None
    _SessionLocal = None


def get_engine():
    """Возвращает singleton Engine."""

    global _engine_singleton, _SessionLocal
    if _engine_singleton is None:
        settings = get_settings()
        _engine_singleton = create_engine(settings.database_url, pool_pre_ping=True)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine_singleton)
    return _engine_singleton


def get_session_factory():
    """Возвращает sessionmaker."""

    get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Зависимость FastAPI: сессия БД."""

    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()
