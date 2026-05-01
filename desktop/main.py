"""Точка входа десктоп-клиента."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from tkinter import messagebox

import customtkinter as ctk

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core import session_store
from src.core.api_client import ApiClient
from src.core.auto_update import check_and_apply_updates
from src.ui.force_password_dialog import ForcePasswordDialog
from src.ui.login import LoginFrame
from src.ui.main_window import MainWindow


def main() -> None:
    """Запуск через сохранённый refresh-токен или окно входа."""

    check_and_apply_updates(ROOT)

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    def proceed_to_main(
        app: ctk.CTk | None,
        client: ApiClient,
        prof: dict[str, Any],
        password_plain: str,
        *,
        remember: bool | None = None,
        login_key: str = "",
    ) -> None:
        if prof.get("must_change_password"):
            if not password_plain:
                messagebox.showwarning(
                    "Учёт производства",
                    "Требуется смена временного пароля — введите текущий пароль в форме входа.",
                )
                return
            assert app is not None
            dlg = ForcePasswordDialog(app, client, password_plain)
            dlg.wait_until_closed()
            prof = client.me()
        try:
            mw = MainWindow(client, prof, data_root=ROOT)
        except Exception as e:
            messagebox.showerror("Учёт производства", f"Не удалось открыть главное окно:\n{e}")
            return
        if remember is not None:
            if remember:
                session_store.save_session(ROOT, client, login_key)
            else:
                session_store.clear(ROOT)
        if app is not None:
            app.destroy()
        mw.mainloop()

    auto_client = ApiClient()
    restored, prof = session_store.try_restore_session(ROOT, auto_client)
    if restored and prof is not None:
        if prof.get("must_change_password"):
            session_store.invalidate_tokens(ROOT)
        else:
            proceed_to_main(None, auto_client, prof, "", remember=None, login_key="")
            return

    app = ctk.CTk()
    app.title("Вход")
    app.geometry("460x420")

    def on_ok(
        client: ApiClient,
        _login_data: dict[str, Any],
        password_plain: str,
        remember: bool,
        login_key: str,
    ) -> None:
        prof = client.me()
        proceed_to_main(app, client, prof, password_plain, remember=remember, login_key=login_key)

    frame = LoginFrame(app, on_ok, prefill_login=session_store.load_last_login(ROOT))
    frame.pack(expand=True, fill="both", padx=24, pady=24)
    app.protocol("WM_DELETE_WINDOW", app.destroy)
    app.mainloop()


if __name__ == "__main__":
    main()
