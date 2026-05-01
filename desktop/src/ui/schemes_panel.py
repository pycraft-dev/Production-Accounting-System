"""Панель схем."""

from __future__ import annotations

import customtkinter as ctk

from src.core.api_client import ApiClient
from src.ui.pdf_viewer import PdfViewer
from src.widgets.data_table import DataTable


class SchemesPanel(ctk.CTkFrame):
    """Версии схем и просмотр PDF с API."""

    def __init__(self, master, client: ApiClient, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.client = client
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(top, text="ID проекта:").pack(side="left")
        self.project_id = ctk.CTkEntry(top, width=80)
        self.project_id.pack(side="left", padx=4)
        ctk.CTkButton(top, text="Список версий", command=self.refresh).pack(side="left", padx=4)
        self.table = DataTable(self, columns=["ID", "Версия", "Статус", "Файл"])
        self.table.pack(fill="both", expand=True, padx=8, pady=4)
        bot = ctk.CTkFrame(self)
        bot.pack(fill="x", padx=8)
        ctk.CTkLabel(bot, text="scheme_id для PDF:").pack(side="left")
        self.scheme_id = ctk.CTkEntry(bot, width=80)
        self.scheme_id.pack(side="left", padx=4)
        ctk.CTkButton(bot, text="Загрузить PDF", command=self.load_pdf).pack(side="left", padx=4)
        self.viewer = PdfViewer(self)
        self.viewer.pack(fill="both", expand=True, padx=8, pady=8)

    def refresh(self) -> None:
        pid = self.project_id.get().strip()
        if not pid.isdigit():
            return
        self.table.clear()
        r = self.client.get(f"/api/schematics/project/{pid}")
        r.raise_for_status()
        for s in r.json():
            self.table.add_row([str(s["id"]), str(s["version"]), s["approval_status"], str(s["file_id"])])

    def load_pdf(self) -> None:
        sid = self.scheme_id.get().strip()
        if not sid.isdigit():
            return
        info = self.client.get(f"/api/schematics/{sid}")
        info.raise_for_status()
        file_id = info.json()["file_id"]
        raw = self.client.get(f"/api/files/{file_id}")
        raw.raise_for_status()
        self.viewer.load_pdf_bytes(raw.content)
