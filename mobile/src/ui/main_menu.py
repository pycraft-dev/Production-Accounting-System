"""Главное меню."""

from __future__ import annotations

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.screen import MDScreen


class MainMenuScreen(MDScreen):
    """Кнопки разделов с учётом роли (например admin видит админку)."""

    def __init__(self, app, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app_ref = app
        self.name = "menu"
        self.root_box = MDBoxLayout(orientation="vertical", padding=16, spacing=8)
        self.add_widget(self.root_box)

    def on_pre_enter(self, *args) -> None:
        self.root_box.clear_widgets()
        app = self.app_ref
        prof = app.profile or {}
        role = prof.get("role", "worker")
        self.root_box.add_widget(MDRaisedButton(text="Брак", on_release=lambda *a: setattr(app.sm, "current", "defect")))
        self.root_box.add_widget(MDRaisedButton(text="Отчёт", on_release=lambda *a: setattr(app.sm, "current", "report")))
        self.root_box.add_widget(MDRaisedButton(text="Схемы", on_release=lambda *a: setattr(app.sm, "current", "schemes")))
        if role == "admin":
            self.root_box.add_widget(
                MDRaisedButton(text="Администрирование", on_release=lambda *a: setattr(app.sm, "current", "admin"))
            )
        self.root_box.add_widget(
            MDRaisedButton(
                text="Синхронизация очереди",
                on_release=lambda *a: app.sync_offline(),
            )
        )
        self.root_box.add_widget(
            MDRaisedButton(
                text="Выйти (сбросить запомненный вход)",
                on_release=lambda *a: app.logout(),
            )
        )
