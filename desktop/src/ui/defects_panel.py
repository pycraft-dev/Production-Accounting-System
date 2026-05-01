"""Панель учёта брака."""

from __future__ import annotations

import mimetypes
import os
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox

from src.core.api_client import ApiClient
from src.widgets.data_table import DataTable
from src.widgets.file_upload import FileUploadZone

# Синхронно с backend/app/constants.py — DEFECT_WORKSHOP_CHOICES
_WORKSHOPS_FALLBACK = ("Барнаул", "Павловск")

_STATUS_RU = {
    "new": "новая",
    "in_progress": "в работе",
    "resolved": "закрыта",
    "rejected": "отклонена",
}


def _open_local_path(path: str) -> None:
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class DefectsPanel(ctk.CTkFrame):
    """Новая заявка (цех из списка, описание, вложения), таблица и дозагрузка к существующей заявке."""

    def __init__(self, master, client: ApiClient, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.client = client
        self._workshops: list[str] = list(_WORKSHOPS_FALLBACK)
        self._new_attachments: list[str] = []

        newf = ctk.CTkFrame(self)
        newf.pack(fill="x", padx=8, pady=6)
        ctk.CTkLabel(newf, text="Новая заявка по браку", font=("", 15, "bold")).pack(anchor="w", pady=(0, 6))
        ctk.CTkLabel(newf, text="Цех").pack(anchor="w")
        self.workshop_menu = ctk.CTkOptionMenu(newf, values=self._workshops, width=300)
        self.workshop_menu.set(self._workshops[0])
        self.workshop_menu.pack(anchor="w", pady=(0, 8))
        ctk.CTkLabel(newf, text="Описание").pack(anchor="w")
        self.desc_box = ctk.CTkTextbox(newf, height=100, width=420)
        self.desc_box.pack(anchor="w", fill="x", pady=(0, 6))
        row = ctk.CTkFrame(newf, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkButton(row, text="Прикрепить фото или видео…", command=self._pick_new_media).pack(
            side="left", padx=(0, 8)
        )
        self.attach_info = ctk.CTkLabel(row, text="Вложений нет")
        self.attach_info.pack(side="left")
        ctk.CTkButton(newf, text="Отправить", command=self._submit_new).pack(anchor="w", pady=8)

        ex = ctk.CTkFrame(self)
        ex.pack(fill="x", padx=8, pady=6)
        ctk.CTkLabel(ex, text="Добавить файл к существующей заявке").pack(anchor="w")
        ctk.CTkLabel(
            ex,
            text="Форматы: JPEG, PNG, WebP, MP4, WebM, MOV (до 50 МБ)",
            text_color="gray",
        ).pack(anchor="w")
        self.defect_id_entry = ctk.CTkEntry(ex, placeholder_text="ID заявки", width=120)
        self.defect_id_entry.pack(anchor="w", padx=8, pady=4)
        self.upload = FileUploadZone(ex, self._on_file_existing)
        self.upload.pack(fill="x", padx=8, pady=4)

        list_bar = ctk.CTkFrame(self, fg_color="transparent")
        list_bar.pack(fill="x", padx=8, pady=(4, 0))
        self._only_mine = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            list_bar,
            text="Только мои заявки",
            variable=self._only_mine,
            command=self.refresh,
        ).pack(side="left")
        ctk.CTkLabel(
            list_bar,
            text="Двойной щелчок по строке — описание и открытие вложений",
            text_color="gray",
        ).pack(side="left", padx=(12, 0))

        self.table = DataTable(
            self,
            columns=["ID", "Цех", "Статус", "Описание"],
            on_row_double_click=self._on_defect_row_double_click,
        )
        self.table.pack(fill="both", expand=True, padx=8, pady=8)
        ctk.CTkButton(self, text="Обновить список", command=self.refresh).pack(pady=4)
        self.refresh()

    def _load_workshops(self) -> None:
        try:
            r = self.client.get("/api/defects/workshops")
            if r.ok:
                data = r.json()
                if isinstance(data, list) and data:
                    self._workshops = data
                    cur = self.workshop_menu.get()
                    self.workshop_menu.configure(values=self._workshops)
                    self.workshop_menu.set(cur if cur in self._workshops else self._workshops[0])
        except Exception:
            pass

    def _pick_new_media(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Фото или видео",
            filetypes=[
                ("Фото и видео", "*.jpg *.jpeg *.png *.webp *.mp4 *.webm *.mov"),
                ("Все файлы", "*.*"),
            ],
        )
        if paths:
            self._new_attachments = list(paths)
            self.attach_info.configure(text=f"Вложений: {len(self._new_attachments)}")

    def _submit_new(self) -> None:
        desc = self.desc_box.get("1.0", "end").strip()
        if not desc:
            messagebox.showwarning("Брак", "Заполните описание.")
            return
        workshop = self.workshop_menu.get()
        body = {
            "description": desc,
            "workshop": workshop,
            "priority": "medium",
            "category": "production",
        }
        try:
            r = self.client.post("/api/defects", json=body)
            if not r.ok:
                messagebox.showerror("Брак", r.text[:400])
                return
            did = r.json()["id"]
            for p in self._new_attachments:
                mime = mimetypes.guess_type(p)[0] or "application/octet-stream"
                with open(p, "rb") as f:
                    files = {"file": (Path(p).name, f, mime)}
                    ur = self.client.post(f"/api/defects/{did}/photos", files=files)
                if not ur.ok:
                    messagebox.showwarning(
                        "Брак",
                        f"Заявка #{did} создана, но файл не загружен: {Path(p).name}\n{ur.text[:200]}",
                    )
            self._new_attachments = []
            self.attach_info.configure(text="Вложений нет")
            self.desc_box.delete("1.0", "end")
            self.refresh()
            messagebox.showinfo("Брак", f"Заявка #{did} отправлена.")
        except Exception as e:
            messagebox.showerror("Брак", str(e))

    def refresh(self) -> None:
        self.table.clear()
        params: dict[str, str | int] = {"limit": 200}
        if self._only_mine.get():
            params["mine"] = "true"
        r = self.client.get("/api/defects", params=params)
        r.raise_for_status()
        for d in r.json():
            if not isinstance(d, dict):
                continue
            st = _STATUS_RU.get(str(d.get("status", "")), str(d.get("status", "")))
            self.table.add_row(
                [str(d["id"]), str(d.get("workshop", "")), st, str(d.get("description", ""))[:80]],
                payload=d,
            )
        self._load_workshops()

    def _on_defect_row_double_click(self, d: dict) -> None:
        did = int(d["id"])

        def work() -> None:
            err: str | None = None
            detail: dict | None = None
            try:
                r = self.client.get(f"/api/defects/{did}")
                if not r.ok:
                    err = r.text[:400]
                else:
                    detail = r.json()
            except Exception as e:
                err = str(e)[:400]

            def show() -> None:
                if err or not isinstance(detail, dict):
                    messagebox.showerror("Брак", err or "Нет данных")
                    return
                self._show_defect_detail_window(detail)

            self.after(0, show)

        threading.Thread(target=work, daemon=True).start()

    def _show_defect_detail_window(self, detail: dict) -> None:
        import tkinter as tk
        from tkinter import font as tkfont
        from tkinter import ttk

        BG = "#2b2b2b"
        PANEL = "#1e1e1e"
        FG = "#ececec"
        MUTED = "#b0b0b0"
        ACCENT = "#2dd4bf"
        BTN = "#0f766e"
        BTN_HOVER = "#14b8a6"

        root = self.winfo_toplevel()
        top = tk.Toplevel(root)
        did = detail.get("id")
        top.title(f"Брак #{did}")
        top.geometry("900x720")
        top.minsize(640, 520)
        top.transient(root)
        top.configure(bg=BG)

        st = _STATUS_RU.get(str(detail.get("status", "")), str(detail.get("status", "")))
        title_f = tkfont.Font(family="Segoe UI", size=20, weight="bold")
        body_f = tkfont.Font(family="Segoe UI", size=12)
        small_f = tkfont.Font(family="Segoe UI", size=11)

        outer = tk.Frame(top, bg=BG, padx=20, pady=16)
        outer.pack(fill="both", expand=True)
        outer.grid_columnconfigure(0, weight=1)

        r = 0
        tk.Label(outer, text=f"Заявка №{did}", font=title_f, fg=ACCENT, bg=BG).grid(
            row=r, column=0, sticky="w"
        )
        r += 1
        meta_fr = tk.Frame(outer, bg=PANEL, padx=16, pady=12)
        meta_fr.grid(row=r, column=0, sticky="ew", pady=(12, 0))
        r += 1
        for key, val in (
            ("Цех", detail.get("workshop")),
            ("Статус", st),
            ("Создана", str(detail.get("created_at", ""))),
        ):
            row_f = tk.Frame(meta_fr, bg=PANEL)
            row_f.pack(fill="x", pady=3)
            tk.Label(row_f, text=f"{key}:", font=small_f, fg=MUTED, bg=PANEL, width=12, anchor="w").pack(
                side="left", padx=(0, 8)
            )
            tk.Label(row_f, text=str(val), font=body_f, fg=FG, bg=PANEL, anchor="w").pack(side="left", fill="x")

        tk.Label(outer, text="Описание", font=body_f, fg=MUTED, bg=BG).grid(
            row=r, column=0, sticky="w", pady=(16, 6)
        )
        r += 1

        frm = tk.Frame(outer, bg=PANEL, highlightthickness=1, highlightbackground="#3d3d3d")
        frm.grid(row=r, column=0, sticky="nsew", pady=(0, 8))
        outer.grid_rowconfigure(r, weight=1)
        r += 1

        txt = tk.Text(
            frm,
            wrap="word",
            height=10,
            width=72,
            font=body_f,
            bg=PANEL,
            fg=FG,
            insertbackground=FG,
            relief=tk.FLAT,
            padx=14,
            pady=12,
            highlightthickness=0,
        )
        ys = ttk.Scrollbar(frm, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(yscrollcommand=ys.set)
        txt.pack(side=tk.LEFT, fill="both", expand=True)
        ys.pack(side=tk.RIGHT, fill=tk.Y)
        txt.insert("1.0", str(detail.get("description", "")))
        txt.configure(state="disabled")

        tk.Label(outer, text="Вложения", font=body_f, fg=MUTED, bg=BG).grid(
            row=r, column=0, sticky="w", pady=(8, 6)
        )
        r += 1
        btn_fr = tk.Frame(outer, bg=BG)
        btn_fs = tkfont.Font(family="Segoe UI", size=12, weight="bold")
        fids = detail.get("attachment_file_ids") or []

        def _style_btn(b: tk.Button) -> None:
            b.configure(
                font=btn_fs,
                bg=BTN,
                fg="#ffffff",
                activebackground=BTN_HOVER,
                activeforeground="#ffffff",
                relief=tk.FLAT,
                padx=20,
                pady=12,
                cursor="hand2",
            )

        if not fids:
            tk.Label(outer, text="Нет файлов", font=small_f, fg=MUTED, bg=BG).grid(
                row=r, column=0, sticky="w"
            )
            r += 1
        else:
            for i, fid in enumerate(fids, 1):
                b = tk.Button(
                    btn_fr,
                    text=f"📎  Открыть вложение {i}  (скачать и показать)",
                    anchor="w",
                    command=lambda f=int(fid): self._download_open_attachment(f),
                )
                _style_btn(b)
                b.pack(fill="x", pady=6)
            btn_fr.grid(row=r, column=0, sticky="ew")
            r += 1

        close_fr = tk.Frame(outer, bg=BG)
        close_fr.grid(row=r, column=0, sticky="e", pady=(16, 0))
        b_close = tk.Button(close_fr, text="Закрыть", command=top.destroy)
        _style_btn(b_close)
        b_close.pack(anchor="e", ipadx=8, ipady=4)

    def _download_open_attachment(self, file_id: int) -> None:
        def work() -> None:
            err: str | None = None
            path: str | None = None
            try:
                r = self.client.get(f"/api/files/{file_id}", timeout=180)
                if not r.ok:
                    err = r.text[:300]
                else:
                    cd = r.headers.get("Content-Disposition") or ""
                    m = re.search(r'filename="([^"]+)"', cd)
                    orig = m.group(1) if m else f"file_{file_id}"
                    suffix = Path(orig).suffix or ".bin"
                    fd, tmp = tempfile.mkstemp(suffix=suffix)
                    os.close(fd)
                    Path(tmp).write_bytes(r.content)
                    path = tmp
            except Exception as e:
                err = str(e)

            def done() -> None:
                if err:
                    messagebox.showerror("Файл", err)
                elif path:
                    try:
                        _open_local_path(path)
                    except Exception as e:
                        messagebox.showerror("Файл", f"Не удалось открыть: {e}\n{path}")

            self.after(0, done)

        threading.Thread(target=work, daemon=True).start()

    def _on_file_existing(self, path: str) -> None:
        did = self.defect_id_entry.get().strip()
        if not did.isdigit():
            messagebox.showwarning("Брак", "Укажите числовой ID заявки.")
            return
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        try:
            with open(path, "rb") as f:
                files = {"file": (Path(path).name, f, mime)}
                r = self.client.post(f"/api/defects/{did}/photos", files=files)
            if r.ok:
                self.refresh()
            else:
                messagebox.showerror("Брак", r.text[:300])
        except Exception as e:
            messagebox.showerror("Брак", str(e))
