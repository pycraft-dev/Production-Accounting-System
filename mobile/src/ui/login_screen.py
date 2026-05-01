"""Экран входа (KivyMD)."""

from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.textfield import MDTextField


class LoginScreen(MDScreen):
    """Поля логин/пароль, запоминание сессии (refresh-токен, без пароля на диске)."""

    def __init__(self, app, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app_ref = app
        self.name = "login"
        root = MDBoxLayout(orientation="vertical", padding=24, spacing=12)
        self.email = MDTextField(hint_text="Логин (admin, worker1…)", mode="rectangle")
        self.password = MDTextField(hint_text="Пароль", password=True, mode="rectangle")
        root.add_widget(self.email)
        root.add_widget(self.password)
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=8)
        self.remember = MDCheckbox(size_hint=(None, None), size=(dp(48), dp(48)))
        self.remember.active = True
        row.add_widget(self.remember)
        row.add_widget(MDLabel(text="Запомнить вход", valign="center", halign="left"))
        root.add_widget(row)
        root.add_widget(MDRaisedButton(text="Войти", on_release=self._do_login))
        self.add_widget(root)

    def on_pre_enter(self, *args) -> None:
        from src.core import session_store

        last = session_store.load_last_login(self.app_ref.data_root)
        if last:
            self.email.text = last

    def _do_login(self, *args) -> None:
        from src.core import session_store

        login_key = self.email.text.strip()
        self.app_ref._remember_login = bool(self.remember.active)
        self.app_ref._login_key_to_save = login_key
        try:
            self.app_ref._temp_login_password = self.password.text
            self.app_ref.api.login(login_key, self.password.text)
            self.app_ref.profile = self.app_ref.api.me()
            if self.app_ref.profile.get("must_change_password"):
                self.app_ref.sm.current = "force_pwd"
                return
            self.app_ref._temp_login_password = ""
            if self.remember.active:
                session_store.save_session(self.app_ref.data_root, self.app_ref.api, login_key)
            else:
                session_store.clear(self.app_ref.data_root)
            self.app_ref.sm.current = "menu"
        except Exception as e:
            self.app_ref.notify(f"Ошибка входа: {e}")
