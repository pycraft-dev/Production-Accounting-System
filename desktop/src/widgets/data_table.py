"""Простая таблица на CustomTkinter."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import customtkinter as ctk


class DataTable(ctk.CTkScrollableFrame):
    """Прокручиваемый список строк (заголовок + значения)."""

    def __init__(
        self,
        master,
        columns: list[str],
        *,
        on_row_double_click: Callable[[Any], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, **kwargs)
        self.columns = columns
        self.on_row_double_click = on_row_double_click
        for j, h in enumerate(columns):
            ctk.CTkLabel(self, text=h, font=ctk.CTkFont(weight="bold")).grid(row=0, column=j, padx=4, pady=2, sticky="w")
        self._row = 1

    def add_row(self, values: list[str], payload: Any = None) -> None:
        """Добавляет строку данных. ``payload`` — для обработчика двойного щелчка (если задан)."""

        row = self._row
        for j, v in enumerate(values):
            lbl = ctk.CTkLabel(self, text=str(v)[:200])
            if self.on_row_double_click is not None and payload is not None:
                lbl.configure(cursor="hand2")
                lbl.bind("<Double-Button-1>", lambda _e, p=payload: self.on_row_double_click(p))
            lbl.grid(row=row, column=j, padx=4, pady=1, sticky="w")
        self._row += 1

    def clear(self) -> None:
        """Очищает строки данных (строка 0 — заголовки)."""

        for w in list(self.winfo_children()):
            info = w.grid_info()
            if info and int(info.get("row", 0)) >= 1:
                w.destroy()
        self._row = 1
