"""Схемы пользователей и администрирования."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import AliasChoices, BaseModel, Field, field_validator
from pydantic.networks import validate_email
from pydantic_core import PydanticCustomError

from app.models.user import UserRole

_LOGIN_SIMPLE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{1,254}$")


class UserCreate(BaseModel):
    """Создание пользователя (только администратор)."""

    login: str = Field(
        ...,
        min_length=3,
        max_length=255,
        validation_alias=AliasChoices("login", "email"),
    )
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=256)
    role: UserRole = UserRole.worker
    profile_notes: str | None = None
    must_change_password: bool = True

    @field_validator("login")
    @classmethod
    def validate_login(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) < 3:
            raise ValueError("Логин не короче 3 символов")
        if "@" in v:
            try:
                _, normalized = validate_email(v)
            except PydanticCustomError as e:
                raise ValueError("Некорректный формат email") from e
            return normalized
        if not _LOGIN_SIMPLE.fullmatch(v):
            raise ValueError(
                "Логин: латиница, цифры, точка, _ и дефис (например admin1), либо полный email"
            )
        return v


class UserUpdate(BaseModel):
    """Частичное обновление профиля."""

    full_name: str | None = Field(default=None, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None
    profile_notes: str | None = None


class UserRead(BaseModel):
    """Пользователь для ответа API."""

    id: int
    login: str = Field(validation_alias="email")
    full_name: str
    role: UserRole
    is_active: bool
    must_change_password: bool
    profile_notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SelfPasswordChange(BaseModel):
    """Смена пароля текущим пользователем."""

    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=8, max_length=256)


class AdminPasswordChange(BaseModel):
    """Смена пароля пользователя администратором."""

    new_password: str = Field(min_length=8, max_length=256)


class AuditLogRead(BaseModel):
    """Запись аудита."""

    id: int
    user_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    details: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
