"""Вспомогательные функции журнала аудита."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def write_audit(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """
    Добавляет запись в аудит (не коммитит транзакцию).

    :param db: сессия SQLAlchemy.
    :param user_id: автор действия (если известен).
    :param action: код действия, например ``defect.create``.
    :param entity_type: тип сущности.
    :param entity_id: идентификатор сущности.
    :param details: дополнительные данные JSON.
    """

    row = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(row)
