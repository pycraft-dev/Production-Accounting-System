"""Главное окно с боковым меню и вкладками модулей."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import customtkinter as ctk

from src.core import session_store
from src.core.api_client import ApiClient
from src.ui.admin_panel import AdminPanel
from src.ui.analytics_panel import AnalyticsPanel
from src.ui.defects_panel import DefectsPanel
from src.ui.reports_panel import ReportsPanel
from src.ui.schemes_panel import SchemesPanel


class MainWindow(ctk.CTk):
    """Основной интерфейс после входа."""

    def __init__(self, client: ApiClient, profile: dict[str, Any], *, data_root: Path | None = None) -> None:
        super().__init__()
        self.client = client
        self.profile = profile
        self._data_root = data_root
        self.title("Учёт производства")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.content = ctk.CTkFrame(self)
        self.content.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)
        role = profile.get("role", "worker")
        self.panels: dict[str, ctk.CTkFrame] = {}
        self._add_nav("Брак", "defects", DefectsPanel(self.content, client))
        self._add_nav("Схемы", "schemes", SchemesPanel(self.content, client))
        self._add_nav("Отчёты", "reports", ReportsPanel(self.content, client))
        self._add_nav("Аналитика", "analytics", AnalyticsPanel(self.content, client))
        if role == "admin":
            self._add_nav("Админ", "admin", AdminPanel(self.content, client))
        self._visible: str | None = None
        self.show("defects")
        self.bind_all("<Control-s>", self._on_ctrl_s)
        self.bind_all("<Control-o>", self._on_ctrl_o)
        self.protocol("WM_DELETE_WINDOW", self._on_wm_close)
        if self._data_root is not None:
            ctk.CTkButton(
                self.sidebar,
                text="Выйти (сбросить запомненный вход)",
                fg_color="transparent",
                border_width=1,
                command=self._logout,
            ).pack(side="bottom", fill="x", padx=8, pady=12)

    def _logout(self) -> None:
        """Стирает сохранённые токены и закрывает окно."""

        if self._data_root is not None:
            session_store.clear(self._data_root)
        try:
            self.quit()
        except Exception:
            pass
        self.destroy()

    def _on_wm_close(self) -> None:
        """Корректное закрытие главного окна по крестику."""

        try:
            self.quit()
        except Exception:
            pass
        self.destroy()

    def _add_nav(self, title: str, key: str, panel: ctk.CTkFrame) -> None:
        self.panels[key] = panel
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_remove()
        btn = ctk.CTkButton(self.sidebar, text=title, command=lambda k=key: self.show(k))
        btn.pack(fill="x", padx=8, pady=6)

    def show(self, key: str) -> None:
        """Переключает видимую панель."""

        if self._visible and self._visible in self.panels:
            self.panels[self._visible].grid_remove()
        self.panels[key].grid()
        self._visible = key

    def _on_ctrl_s(self, _evt: object) -> None:
        """Сохранение черновика отчёта."""

        rep = self.panels.get("reports")
        if rep is not None and hasattr(rep, "quick_save"):
            rep.quick_save()

    def _on_ctrl_o(self, _evt: object) -> None:
        """Фокус на модуль с файлами (брак)."""

        self.show("defects")
