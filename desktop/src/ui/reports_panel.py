"""Панель ежедневных отчётов."""

from __future__ import annotations

from datetime import date

import customtkinter as ctk

from src.core.api_client import ApiClient
from src.widgets.data_table import DataTable


class ReportsPanel(ctk.CTkFrame):
    """Чек-листы отчётов."""

    def __init__(self, master, client: ApiClient, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.client = client
        self.table = DataTable(self, columns=["ID", "Дата", "Статус", "Смена"])
        self.table.pack(fill="both", expand=True, padx=8, pady=8)
        ctk.CTkButton(self, text="Обновить", command=self.refresh).pack(pady=4)
        ctk.CTkButton(self, text="Черновик на сегодня (Ctrl+S)", command=self.quick_save).pack(pady=4)
        self.refresh()

    def refresh(self) -> None:
        self.table.clear()
        r = self.client.get("/api/daily-reports")
        r.raise_for_status()
        for row in r.json():
            self.table.add_row([str(row["id"]), str(row["report_date"]), row["status"], str(row.get("shift_name") or "")])

    def quick_save(self) -> None:
        """Создаёт короткий черновик отчёта на сегодня (горячая клавиша)."""

        today = date.today().isoformat()
        payload = {
            "report_date": today,
            "tasks_checklist": [{"text": "Задача 1", "done": False}],
            "status": "draft",
        }
        r = self.client.post("/api/daily-reports", json=payload)
        if r.ok:
            self.refresh()
