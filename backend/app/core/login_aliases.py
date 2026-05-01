"""Подбор идентификатора учётной записи для входа (логин хранится в ``User.email``)."""

from __future__ import annotations

# Старые демо-учётки с суффиксом @example.com: короткое имя всё ещё находит запись.
_LEGACY_SHORT_TO_FULL: dict[str, str] = {
    "admin": "admin@example.com",
    "worker1": "worker1@example.com",
    "constructor1": "constructor1@example.com",
}


def login_lookup_keys(raw_login: str) -> list[str]:
    """
    Возвращает строки для поиска в колонке ``users.email``.

    Порядок: как ввели, затем (для коротких имён без ``@``) — вариант из legacy-мапы,
    если он отличается.
    """

    s = raw_login.strip()
    if not s:
        return []
    if "@" in s:
        return [s]
    keys = [s]
    legacy = _LEGACY_SHORT_TO_FULL.get(s.lower())
    if legacy is not None and legacy not in keys:
        keys.append(legacy)
    return keys
