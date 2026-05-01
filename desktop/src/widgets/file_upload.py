"""Зона выбора файла (кнопка + опционально drag&drop через проводник)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog


class FileUploadZone(ctk.CTkFrame):
    """Виджет: кнопка «Выбрать файл» и подсказка."""

    def __init__(self, master, on_path: Callable[[str], None], **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.on_path = on_path
        ctk.CTkLabel(self, text="Файлы: нажмите «Выбрать файл»").pack(pady=4)
        ctk.CTkButton(self, text="Выбрать файл…", command=self._pick).pack(pady=4)

    def _pick(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[
                ("Фото и видео", "*.jpg *.jpeg *.png *.webp *.mp4 *.webm *.mov"),
                ("Все", "*.*"),
            ],
        )
        if path:
            self.on_path(path)

    def emit_path(self, path: str) -> None:
        """Вызывается извне при drop файла (если реализовано на уровне окна)."""

        if Path(path).is_file():
            self.on_path(path)
