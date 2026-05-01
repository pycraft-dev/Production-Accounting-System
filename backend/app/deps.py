"""Зависимости FastAPI: БД, пользователь, RBAC."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.database import get_db
from app.models.user import User, UserRole

security = HTTPBearer(auto_error=False)


def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    """Возвращает пользователя по Bearer-токену или None."""

    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            return None
        sub = payload.get("sub")
        if not sub:
            return None
        user_id = int(sub)
    except (JWTError, ValueError, TypeError):
        return None
    user = db.get(User, user_id)
    if not user or not user.is_active:
        return None
    return user


def get_current_user(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User:
    """Требует валидный access-токен."""

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация")
    return user


def require_role(*roles: UserRole):
    """Фабрика зависимостей: доступ только для перечисленных ролей."""

    allowed = set(roles)

    def _inner(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        return user

    return _inner


def require_any_role(*roles: UserRole):
    """Алиас для читаемости (то же, что require_role)."""

    return require_role(*roles)
