"""Панель аналитики."""

from __future__ import annotations

from datetime import date, timedelta

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.core.api_client import ApiClient


class AnalyticsPanel(ctk.CTkFrame):
    """График OEE (упрощённо)."""

    def __init__(self, master, client: ApiClient, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.client = client
        ctk.CTkButton(self, text="Загрузить OEE (30 дней)", command=self.load_oee).pack(pady=8)
        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        ctk.CTkButton(self, text="Экспорт Excel брака", command=self.export_xlsx).pack(pady=4)

    def load_oee(self) -> None:
        to_d = date.today()
        from_d = to_d - timedelta(days=30)
        r = self.client.post(
            "/api/analytics/oee",
            json={"date_from": from_d.isoformat(), "date_to": to_d.isoformat(), "equipment_id": None},
        )
        r.raise_for_status()
        d = r.json()
        self.ax.clear()
        names = ["Доступность", "Производительность", "Качество", "OEE"]
        vals = [d["availability"], d["performance"], d["quality"], d["oee"]]
        self.ax.bar(names, vals, color=["#4e79a7", "#f28e2b", "#e15759", "#76b7b2"])
        self.ax.set_ylim(0, 1)
        self.figure.tight_layout()
        self.canvas.draw()

    def export_xlsx(self) -> None:
        r = self.client.get("/api/export/defects", params={"fmt": "xlsx"})
        if r.ok:
            with open("export_defects.xlsx", "wb") as f:
                f.write(r.content)
