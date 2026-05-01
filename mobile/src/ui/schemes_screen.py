"""Список версий схем."""

from __future__ import annotations

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField


class SchemesScreen(MDScreen):
    """Запрос списка версий по ID проекта."""

    def __init__(self, app, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app_ref = app
        self.name = "schemes"
        root = MDBoxLayout(orientation="vertical", padding=16, spacing=8)
        self.pid = MDTextField(hint_text="ID проекта", mode="rectangle")
        root.add_widget(self.pid)
        root.add_widget(MDRaisedButton(text="Загрузить список", on_release=self._load))
        self.out = MDLabel(text="", halign="left")
        root.add_widget(self.out)
        self.add_widget(root)

    def _load(self, *a) -> None:
        pid = self.pid.text.strip()
        if not pid:
            return
        try:
            r = self.app_ref.api.session.get(
                f"{self.app_ref.api.base_url}/api/schematics/project/{pid}",
                timeout=60,
            )
            r.raise_for_status()
            lines = [f"v{s['version']} — {s['approval_status']}" for s in r.json()[:20]]
            self.out.text = "\n".join(lines) or "Пусто"
        except Exception as e:
            self.out.text = str(e)
