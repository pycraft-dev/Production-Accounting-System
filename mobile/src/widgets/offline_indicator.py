"""Индикатор оффлайна (показ в шапке при необходимости)."""

from __future__ import annotations

from kivymd.uix.label import MDLabel


def offline_chip(count: int) -> MDLabel:
    """Возвращает виджет с числом задач в очереди."""

    return MDLabel(text=f"Оффлайн: {count} в очереди", halign="center")
