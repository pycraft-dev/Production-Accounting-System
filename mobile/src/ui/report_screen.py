"""Ежедневный отчёт (мобильный)."""

from __future__ import annotations

from datetime import date

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen


class ReportScreen(MDScreen):
    """Чек-лист из одной задачи и дата."""

    def __init__(self, app, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app_ref = app
        self.name = "report"
        root = MDBoxLayout(orientation="vertical", padding=16, spacing=8)
        self.lbl = MDLabel(text="", halign="center")
        root.add_widget(self.lbl)
        root.add_widget(MDRaisedButton(text="Создать черновик на сегодня", on_release=self._create))
        self.add_widget(root)
        self.bind(on_enter=self._on_enter)

    def _on_enter(self, *a) -> None:
        self.lbl.text = f"Дата: {date.today().strftime('%d.%m.%Y')}"

    def _create(self, *a) -> None:
        payload = {
            "report_date": date.today().isoformat(),
            "tasks_checklist": [{"text": "Задача (моб.)", "done": False}],
            "status": "draft",
        }
        try:
            r = self.app_ref.api.post("/api/daily-reports", json_body=payload, offline_fallback=True)
            r.raise_for_status()
            self.app_ref.notify("Отчёт сохранён")
        except Exception:
            self.app_ref.notify("В очередь оффлайна")
