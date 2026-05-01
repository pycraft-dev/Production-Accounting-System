"""Экран входа."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import customtkinter as ctk
import requests
from tkinter import messagebox

from src.core.api_client import ApiClient


class LoginFrame(ctk.CTkFrame):
    """Форма авторизации."""

    def __init__(
        self,
        master,
        on_success: Callable[[ApiClient, dict[str, Any], str, bool, str], None],
        *,
        prefill_login: str = "",
    ) -> None:
        super().__init__(master)
        self.on_success = on_success
        self.client = ApiClient()
        self.email = ctk.CTkEntry(self, placeholder_text="Логин (например admin или worker1)", width=280)
        self.password = ctk.CTkEntry(self, placeholder_text="Пароль", show="*", width=280)
        if prefill_login:
            self.email.insert(0, prefill_login)
        self.btn = ctk.CTkButton(self, text="Войти", command=self._login)
        self.remember = ctk.CTkCheckBox(self, text="Запомнить вход (без повторного пароля до истечения сессии)")
        self.remember.select()
        self.err = ctk.CTkLabel(self, text="", text_color="red")
        self.email.pack(pady=8)
        self.password.pack(pady=8)
        self.remember.pack(pady=4)
        self.btn.pack(pady=12)
        self.err.pack()

    def _login(self) -> None:
        """Отправляет учётные данные на API."""

        try:
            login_key = self.email.get().strip()
            login_data = self.client.login(login_key, self.password.get())
            self.err.configure(text="")
            rv = self.remember.get()
            remember = rv not in (0, "off", False, "", None)
            self.on_success(self.client, login_data, self.password.get(), remember, login_key)
        except requests.exceptions.ConnectionError:
            msg = (
                "Сервер не запущен или недоступен. Сначала запустите API "
                "(launcher.bat → «Запустить сервер» или start_server.bat в корне проекта)."
            )
            try:
                self.err.configure(text=msg)
            except Exception:
                messagebox.showerror("Учёт производства", msg)
        except requests.exceptions.Timeout:
            msg = "Сервер не отвечает (таймаут). Проверьте адрес API и сеть."
            try:
                self.err.configure(text=msg)
            except Exception:
                messagebox.showerror("Учёт производства", msg)
        except Exception as e:
            try:
                self.err.configure(text=f"Ошибка входа: {e}")
            except Exception:
                messagebox.showerror("Учёт производства", f"Ошибка входа: {e}")
