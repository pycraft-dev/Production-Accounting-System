"""Схемы авторизации и токенов."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class LoginRequest(BaseModel):
    """
    Запрос входа.

    В JSON допустимы поля ``login`` или ``email`` (алиас, то же значение).
    Логин в системе — строка вида ``admin``, ``admin1``, ``worker2`` или полный email (если так создана учётка).
    """

    login: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=256)

    @model_validator(mode="before")
    @classmethod
    def _email_alias(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("login") is None and data.get("email") is not None:
            return {**data, "login": data["email"]}
        return data


class TokenPair(BaseModel):
    """Пара access/refresh JWT."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    must_change_password: bool = False


class RefreshRequest(BaseModel):
    """Запрос обновления access-токена."""

    refresh_token: str
