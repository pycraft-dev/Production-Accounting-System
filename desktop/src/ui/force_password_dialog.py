"""Обязательная смена пароля при первом входе (модальное окно)."""

from __future__ import annotations

import customtkinter as ctk

from src.core.api_client import ApiClient


class ForcePasswordDialog(ctk.CTkToplevel):
    """Диалог смены пароля, блокирует закрытие до успешного запроса или отмены."""

    def __init__(self, master: ctk.CTk, client: ApiClient, current_password: str) -> None:
        super().__init__(master)
        self.client = client
        self._current = current_password
        self.title("Смена пароля")
        self.geometry("400x280")
        self.resizable(False, False)
        self._done = False
        msg = ctk.CTkLabel(
            self,
            text="Смените пароль учётной записи (минимум 8 символов).",
            wraplength=360,
        )
        msg.pack(padx=16, pady=(16, 8))
        self.new_pwd = ctk.CTkEntry(self, placeholder_text="Новый пароль", show="*", width=300)
        self.new_pwd2 = ctk.CTkEntry(self, placeholder_text="Повтор пароля", show="*", width=300)
        self.new_pwd.pack(pady=4)
        self.new_pwd2.pack(pady=4)
        self.err = ctk.CTkLabel(self, text="", text_color="red")
        self.err.pack(pady=4)
        ctk.CTkButton(self, text="Сохранить", command=self._save).pack(pady=8)
        self.transient(master)
        self.grab_set()
        self.protocol(
            "WM_DELETE_WINDOW",
            lambda: self.err.configure(
                text="Сначала задайте новый пароль и нажмите «Сохранить».",
            ),
        )

    def _save(self) -> None:
        a, b = self.new_pwd.get(), self.new_pwd2.get()
        if len(a) < 8:
            self.err.configure(text="Пароль не короче 8 символов")
            return
        if a != b:
            self.err.configure(text="Пароли не совпадают")
            return
        try:
            self.client.change_password(self._current, a)
        except Exception as e:
            self.err.configure(text=str(e))
            return
        self._done = True
        self.grab_release()
        self.destroy()

    def wait_until_closed(self) -> bool:
        """Блокирует до закрытия; True если пароль сменён."""

        self.master.wait_window(self)
        return self._done
