"""Точка входа KivyMD."""

from __future__ import annotations

import sys
from pathlib import Path

from kivy.clock import Clock

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp

from src.core.api_client import MobileApiClient
from src.core.auto_update import schedule_update_check
from src.ui.admin_screen import AdminScreen, ForcePasswordScreen
from src.ui.defect_screen import DefectScreen
from src.ui.login_screen import LoginScreen
from src.ui.main_menu import MainMenuScreen
from src.ui.report_screen import ReportScreen
from src.ui.schemes_screen import SchemesScreen


class PasApp(MDApp):
    """Корневое приложение."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.data_root = ROOT
        self.api = MobileApiClient(queue_path=str(ROOT / "data" / "offline_queue.db"))
        self.profile: dict = {}
        self._remember_login = False
        self._login_key_to_save = ""

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        sm = ScreenManager()
        self.sm = sm
        sm.add_widget(LoginScreen(self))
        sm.add_widget(ForcePasswordScreen(self))
        sm.add_widget(MainMenuScreen(self))
        sm.add_widget(AdminScreen(self))
        sm.add_widget(DefectScreen(self))
        sm.add_widget(ReportScreen(self))
        sm.add_widget(SchemesScreen(self))
        sm.current = "login"
        Clock.schedule_once(lambda _dt: self._try_restore_session(), 0)
        return sm

    def on_start(self) -> None:
        schedule_update_check(self, Path(__file__).resolve().parent)

    def _try_restore_session(self) -> None:
        from src.core import session_store

        restored, prof = session_store.try_restore_session(self.data_root, self.api)
        if not restored or not prof:
            return
        if prof.get("must_change_password"):
            session_store.invalidate_tokens(self.data_root)
            return
        self.profile = prof
        if self.sm:
            self.sm.current = "menu"

    def logout(self) -> None:
        """Сброс сессии и возврат на экран входа."""

        from src.core import session_store

        self.api.access_token = None
        self.api.refresh_token = None
        self.api.session.headers.pop("Authorization", None)
        session_store.clear(self.data_root)
        self.profile = {}
        self.sm.current = "login"

    def notify(self, msg: str) -> None:
        """Локальное уведомление (plyer при наличии)."""

        title = "Учёт производства"
        max_title, max_body = 63, 240
        t = title if len(title) <= max_title else title[: max_title - 1] + "…"
        body = (msg or "").strip()
        if len(body) > max_body:
            body = body[: max_body - 3] + "..."

        try:
            from plyer import notification

            notification.notify(title=t, message=body, timeout=3)
        except Exception:
            print(msg)

    def sync_offline(self) -> None:
        """Отправка оффлайн-очереди."""

        n = self.api.sync_queue()
        self.notify(f"Синхронизировано записей: {n}")


def main() -> None:
    PasApp().run()


if __name__ == "__main__":
    main()
