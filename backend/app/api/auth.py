"""Авторизация: вход, refresh; регистрация отключена."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.users import SelfPasswordChange, UserRead
from app.core.login_aliases import login_lookup_keys
from app.utils.audit import write_audit
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair

router = APIRouter(prefix="/auth", tags=["Авторизация"])


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    """Выдаёт пару JWT при успешной аутентификации."""

    user = None
    for key in login_lookup_keys(payload.login):
        user = db.scalar(select(User).where(User.email == key))
        if user is not None:
            break
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Учётная запись отключена")
    write_audit(
        db,
        user_id=user.id,
        action="auth.login",
        entity_type="Session",
        entity_id=None,
        details={"login": user.email},
    )
    db.commit()
    sub = str(user.id)
    return TokenPair(
        access_token=create_access_token({"sub": sub}),
        refresh_token=create_refresh_token({"sub": sub}),
        must_change_password=user.must_change_password,
    )


@router.post("/refresh", response_model=TokenPair)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    """Обновляет access-токен по действительному refresh-токену."""

    try:
        data = decode_token(payload.refresh_token)
        if data.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный тип токена")
        sub = data.get("sub")
        user_id = int(sub)
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный refresh-токен")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    sub = str(user.id)
    return TokenPair(
        access_token=create_access_token({"sub": sub}),
        refresh_token=create_refresh_token({"sub": sub}),
        must_change_password=user.must_change_password,
    )


@router.get("/me", response_model=UserRead)
def me(current: Annotated[User, Depends(get_current_user)]) -> User:
    """Текущий пользователь по access-токену."""

    return current


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_own_password(
    payload: SelfPasswordChange,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Смена пароля текущим пользователем (сбрасывает флаг принудительной смены)."""

    if not verify_password(payload.current_password, current.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный текущий пароль")
    current.hashed_password = hash_password(payload.new_password)
    current.must_change_password = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/register", status_code=status.HTTP_403_FORBIDDEN)
def register_disabled() -> None:
    """Публичная регистрация отключена."""

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Регистрация отключена. Обратитесь к администратору.",
    )
