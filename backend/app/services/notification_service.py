"""Отправка уведомлений Email и Telegram с записью ошибок в лог."""

from __future__ import annotations

import logging
from email.message import EmailMessage

import httpx
from aiosmtplib import SMTP

from app.core.config import get_settings
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


def _looks_like_email(addr: str) -> bool:
    """SMTP: в колонке логина может быть не email — такие адреса пропускаем."""

    if not addr or "@" not in addr:
        return False
    host = addr.split("@", 1)[-1]
    return "." in host


def _roles_from_setting(raw: str) -> set[UserRole]:
    """Парсит список ролей из строки окружения."""

    out: set[UserRole] = set()
    for part in raw.split(","):
        p = part.strip()
        if not p:
            continue
        try:
            out.add(UserRole(p))
        except ValueError:
            logger.warning("Неизвестная роль в настройках уведомлений: %s", p)
    return out


def should_notify_for_defect(role: UserRole) -> bool:
    """Проверяет, нужно ли слать уведомление о браке для роли."""

    settings = get_settings()
    return role in _roles_from_setting(settings.notify_roles_defect_created)


def should_notify_for_scheme(role: UserRole) -> bool:
    """Проверяет уведомления об изменении схемы."""

    settings = get_settings()
    return role in _roles_from_setting(settings.notify_roles_scheme_updated)


async def send_email(subject: str, body: str, to_addresses: list[str]) -> None:
    """
    Отправляет письмо через SMTP (async).

    При ошибке логирует и не пробрасывает исключение наружу (fallback в лог).
    """

    settings = get_settings()
    if not settings.smtp_host or not to_addresses:
        logger.info("SMTP не настроен или нет получателей — письмо пропущено")
        return
    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = ", ".join(to_addresses)
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        smtp = SMTP(
            hostname=settings.smtp_host,
            port=settings.smtp_port,
        )
        await smtp.connect()
        if settings.smtp_tls:
            await smtp.starttls()
        if settings.smtp_user:
            await smtp.login(settings.smtp_user, settings.smtp_password)
        await smtp.send_message(msg)
        await smtp.quit()
    except Exception:
        logger.exception("Ошибка отправки email: %s", subject)


async def send_telegram(text: str) -> None:
    """Отправляет сообщение в Telegram; при ошибке пишет в лог."""

    settings = get_settings()
    token = settings.telegram_bot_token
    chat = settings.telegram_chat_id
    if not token or not chat:
        logger.info("Telegram не настроен — сообщение пропущено")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(url, json={"chat_id": chat, "text": text})
            r.raise_for_status()
    except Exception:
        logger.exception("Ошибка отправки Telegram")


async def notify_defect_created(users: list[User], title: str, defect_id: int) -> None:
    """
    Рассылает уведомления о новом браке по матрице ролей.

    :param users: все активные пользователи (или отфильтрованный список).
    :param title: краткий текст.
    :param defect_id: идентификатор заявки.
    """

    targets = [u for u in users if u.is_active and should_notify_for_defect(u.role)]
    emails = [u.email for u in targets if _looks_like_email(u.email)]
    body = f"Новая заявка по браку #{defect_id}: {title}"
    await send_email("Новая заявка по браку", body, emails)
    await send_telegram(body)


async def notify_scheme_updated(users: list[User], project_name: str, version: int) -> None:
    """Уведомляет об обновлении версии схемы."""

    targets = [u for u in users if u.is_active and should_notify_for_scheme(u.role)]
    emails = [u.email for u in targets if _looks_like_email(u.email)]
    body = f"Обновлена схема проекта «{project_name}», версия {version}"
    await send_email("Обновление схемы", body, emails)
    await send_telegram(body)
