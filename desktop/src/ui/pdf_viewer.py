"""Просмотр PDF (рендер страницы через PyMuPDF)."""

from __future__ import annotations

from io import BytesIO

import customtkinter as ctk
from PIL import Image, ImageTk

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore


class PdfViewer(ctk.CTkFrame):
    """Показывает первую страницу PDF в виджете CTkLabel (масштаб)."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.label = ctk.CTkLabel(self, text="PDF не загружен")
        self.label.pack(fill="both", expand=True)
        self._photo: ImageTk.PhotoImage | None = None

    def load_pdf_bytes(self, data: bytes, page_index: int = 0) -> None:
        """Рендерит страницу PDF из памяти."""

        if fitz is None:
            self.label.configure(text="Установите pymupdf для просмотра PDF")
            return
        doc = fitz.open(stream=data, filetype="pdf")
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.open(BytesIO(pix.tobytes("png")))
        img.thumbnail((900, 700))
        self._photo = ImageTk.PhotoImage(img)
        self.label.configure(text="", image=self._photo)

    def set_message(self, text: str) -> None:
        """Показывает текст вместо документа."""

        self.label.configure(text=text, image="")
