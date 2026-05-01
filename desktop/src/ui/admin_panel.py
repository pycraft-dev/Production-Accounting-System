"""Панель администратора."""

from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import customtkinter as ctk

from src.core.api_client import ApiClient
from src.widgets.data_table import DataTable


def _next_login_for_role(users: list[dict], role: str) -> str:
    """Следующий свободный логин вида admin1, worker2 по данным списка пользователей."""

    nums: list[int] = []
    for u in users:
        log = str(u.get("login") or "")
        if not log.startswith(role):
            continue
        suffix = log[len(role) :]
        if suffix.isdigit():
            nums.append(int(suffix))
    n = max(nums) + 1 if nums else 1
    return f"{role}{n}"


def _format_api_error(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return "Ошибка сервера"
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text[:400]
    detail = data.get("detail")
    if isinstance(detail, str):
        return detail[:400]
    if isinstance(detail, list):
        parts: list[str] = []
        for item in detail:
            if isinstance(item, dict):
                msg = item.get("msg") or item.get("message")
                loc = item.get("loc")
                if msg and isinstance(loc, (list, tuple)):
                    loc_s = ".".join(str(x) for x in loc[-2:] if x != "body")
                    parts.append(f"{loc_s}: {msg}" if loc_s else str(msg))
                elif msg:
                    parts.append(str(msg))
        if parts:
            return "; ".join(parts)[:400]
    errs = data.get("errors")
    if isinstance(errs, list):
        parts = [str(e.get("msg", "")) for e in errs if isinstance(e, dict) and e.get("msg")]
        if parts:
            return "; ".join(parts)[:400]
    return text[:400]


class AdminPanel(ctk.CTkFrame):
    """Пользователи и аудит."""

    def __init__(self, master, client: ApiClient, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.client = client
        self.users_cache: list[dict] = []

        self.users_table = DataTable(self, columns=["ID", "Логин", "Имя", "Роль", "Активен"])
        self.users_table.pack(fill="both", expand=True, padx=8, pady=4)

        row = ctk.CTkFrame(self)
        row.pack(fill="x", padx=8)
        self.user_id_entry = ctk.CTkEntry(row, placeholder_text="ID пользователя", width=100)
        self.user_id_entry.pack(side="left", padx=4)
        ctk.CTkButton(row, text="Создать…", width=100, command=self._create_user).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Применить роль/активн.", width=150, command=self._apply_patch).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Сменить пароль…", width=130, command=self._change_pwd).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Отключить", width=100, command=self._deactivate).pack(side="left", padx=4)

        self.role_var = ctk.StringVar(value="worker")
        ctk.CTkLabel(row, text="Роль:").pack(side="left", padx=(12, 2))
        self.role_menu = ctk.CTkOptionMenu(row, values=["admin", "worker", "constructor"], variable=self.role_var)
        self.role_menu.pack(side="left", padx=4)
        self.active_var = ctk.StringVar(value="да")
        ctk.CTkLabel(row, text="Активен:").pack(side="left", padx=(8, 2))
        self.active_menu = ctk.CTkOptionMenu(row, values=["да", "нет"], variable=self.active_var)
        self.active_menu.pack(side="left", padx=4)

        self.audit_table = DataTable(self, columns=["Время", "Действие", "Сущность", "user_id"])
        self.audit_table.pack(fill="both", expand=True, padx=8, pady=4)
        ctk.CTkButton(self, text="Обновить", command=self.refresh).pack(pady=4)
        ctk.CTkButton(self, text="Синхронизация ERP", command=self.erp_sync).pack(pady=4)
        ctk.CTkButton(self, text="Документация (все файлы из docs/)", command=self._open_docs).pack(pady=4)
        self.refresh()

    def refresh(self) -> None:
        self.users_table.clear()
        ru = self.client.get("/api/admin/users")
        if ru.ok:
            self.users_cache = ru.json()
            for u in self.users_cache:
                self.users_table.add_row(
                    [
                        str(u["id"]),
                        u.get("login", ""),
                        u.get("full_name", ""),
                        u["role"],
                        "да" if u.get("is_active") else "нет",
                    ]
                )
        self.audit_table.clear()
        ra = self.client.get("/api/admin/audit", params={"limit": 40})
        if ra.ok:
            for a in ra.json():
                self.audit_table.add_row(
                    [
                        str(a["created_at"]),
                        a["action"],
                        a["entity_type"],
                        str(a.get("user_id", "")),
                    ]
                )

    def _selected_id(self) -> int | None:
        raw = self.user_id_entry.get().strip()
        if not raw.isdigit():
            messagebox.showwarning("Учёт производства", "Укажите числовой ID пользователя.")
            return None
        return int(raw)

    def _create_user(self) -> None:
        """Диалог создания пользователя на базе tkinter (CTkToplevel на Windows часто пустой и не закрывается)."""

        root = self.winfo_toplevel()
        bg, fg = "#2b2b2b", "#ececec"
        top = tk.Toplevel(root)
        top.title("Новый пользователь")
        top.resizable(False, False)
        top.transient(root)
        top.configure(bg=bg)
        top.geometry("470x440")

        def close_dialog() -> None:
            try:
                top.destroy()
            except Exception:
                pass

        top.protocol("WM_DELETE_WINDOW", close_dialog)

        frm = tk.Frame(top, bg=bg, padx=18, pady=14)
        frm.pack(fill="both", expand=True)

        def mk_lbl(t: str) -> None:
            tk.Label(frm, text=t, bg=bg, fg=fg, anchor="w").pack(fill="x", pady=(10, 2))

        mk_lbl("Роль")
        role_c = ttk.Combobox(frm, values=["admin", "worker", "constructor"], state="readonly", width=49)
        role_c.set("worker")
        role_c.pack(fill="x", pady=(0, 4))
        mk_lbl("Логин (подставляется по роли: admin1, worker2…)")
        login_e = tk.Entry(frm, width=52)
        login_e.pack(fill="x")

        def sync_login_from_role(_event: object | None = None) -> None:
            rname = role_c.get() or "worker"
            login_e.delete(0, tk.END)
            login_e.insert(0, _next_login_for_role(self.users_cache, rname))

        role_c.bind("<<ComboboxSelected>>", sync_login_from_role)

        mk_lbl("ФИО")
        name_e = tk.Entry(frm, width=52)
        name_e.pack(fill="x")
        mk_lbl("Пароль (не короче 8 символов)")
        pwd_e = tk.Entry(frm, width=52, show="*")
        pwd_e.pack(fill="x")
        err_var = tk.StringVar(value="")
        err_lbl = tk.Label(frm, textvariable=err_var, bg=bg, fg="#ff6b6b", wraplength=420, justify="left")
        err_lbl.pack(fill="x", pady=8)

        sync_login_from_role()

        def save() -> None:
            body = {
                "login": login_e.get().strip(),
                "full_name": name_e.get().strip(),
                "password": pwd_e.get(),
                "role": role_c.get() or "worker",
            }
            r = self.client.post("/api/admin/users", json=body)
            if not r.ok:
                err_var.set(_format_api_error(r.text))
                return
            close_dialog()
            self.refresh()

        btns = tk.Frame(frm, bg=bg)
        btns.pack(fill="x", pady=(12, 0))
        tk.Button(btns, text="Отмена", width=14, command=close_dialog).pack(side="left", padx=(0, 8))
        tk.Button(btns, text="Создать", width=14, command=save).pack(side="left")

        top.update_idletasks()
        top.lift()
        top.focus_force()

    def _apply_patch(self) -> None:
        uid = self._selected_id()
        if uid is None:
            return
        body = {
            "role": self.role_var.get(),
            "is_active": self.active_var.get() == "да",
        }
        r = self.client.patch(f"/api/admin/users/{uid}", json=body)
        if not r.ok:
            messagebox.showerror("Учёт производства", r.text[:300])
            return
        self.refresh()

    def _change_pwd(self) -> None:
        uid = self._selected_id()
        if uid is None:
            return
        parent = self.winfo_toplevel()
        pwd = simpledialog.askstring("Пароль", "Новый пароль (≥8 символов):", show="*", parent=parent)
        if not pwd or len(pwd) < 8:
            return
        r = self.client.post(f"/api/admin/users/{uid}/change-password", json={"new_password": pwd})
        if not r.ok:
            messagebox.showerror("Учёт производства", r.text[:300])
            return
        messagebox.showinfo("Учёт производства", "Пароль обновлён")
        self.refresh()

    def _deactivate(self) -> None:
        uid = self._selected_id()
        if uid is None:
            return
        if not messagebox.askyesno("Учёт производства", "Отключить этого пользователя?"):
            return
        r = self.client.delete(f"/api/admin/users/{uid}")
        if not r.ok:
            messagebox.showerror("Учёт производства", r.text[:300])
            return
        self.refresh()

    def erp_sync(self) -> None:
        r = self.client.post("/api/erp/import")
        if not r.ok:
            messagebox.showwarning("ERP", r.text[:200])

    def _open_docs(self) -> None:
        """Просмотр markdown из каталога docs/ на сервере (только через API)."""

        root = self.winfo_toplevel()
        top = tk.Toplevel(root)
        top.title("Документация (docs)")
        top.geometry("920x660")
        top.transient(root)
        bg, fg = "#2b2b2b", "#ececec"
        top.configure(bg=bg)

        pan = tk.PanedWindow(top, orient=tk.HORIZONTAL, bg=bg, sashwidth=5)
        pan.pack(fill="both", expand=True, padx=6, pady=6)

        left = tk.Frame(pan, bg=bg)
        right = tk.Frame(pan, bg=bg)
        pan.add(left, minsize=200)
        pan.add(right)

        tk.Label(left, text="Файлы", bg=bg, fg=fg).pack(anchor="w")
        lb_frame = tk.Frame(left, bg=bg)
        lb_frame.pack(fill="both", expand=True)
        lb = tk.Listbox(lb_frame, bg="#1e1e1e", fg=fg, selectmode=tk.SINGLE, width=32, exportselection=False)
        slb = ttk.Scrollbar(lb_frame, orient=tk.VERTICAL, command=lb.yview)
        lb.configure(yscrollcommand=slb.set)
        lb.pack(side=tk.LEFT, fill="both", expand=True)
        slb.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(right, text="Содержимое", bg=bg, fg=fg).pack(anchor="w")
        txt_frame = tk.Frame(right, bg=bg)
        txt_frame.pack(fill="both", expand=True)
        txt = tk.Text(txt_frame, wrap="word", bg="#1e1e1e", fg=fg, insertbackground=fg, font=("Consolas", 10))
        st = ttk.Scrollbar(txt_frame, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(yscrollcommand=st.set)
        txt.pack(side=tk.LEFT, fill="both", expand=True)
        st.pack(side=tk.RIGHT, fill=tk.Y)

        items: list[tuple[str, str]] = []
        r = self.client.get("/api/admin/docs")
        if not r.ok:
            txt.insert("1.0", f"Не удалось загрузить список документов:\n{r.text[:1500]}")
            txt.configure(state="disabled")
            tk.Button(top, text="Закрыть", command=top.destroy).pack(pady=4)
            return
        for d in r.json():
            fn = str(d.get("filename", ""))
            title = str(d.get("title", fn))
            if fn:
                items.append((fn, title))
                lb.insert(tk.END, title)

        def on_sel(_event: object | None = None) -> None:
            sel = lb.curselection()
            if not sel:
                return
            fn, _ = items[sel[0]]
            rr = self.client.get(f"/api/admin/docs/{fn}")
            txt.configure(state="normal")
            txt.delete("1.0", tk.END)
            if rr.ok:
                txt.insert("1.0", rr.text)
            else:
                txt.insert("1.0", rr.text[:8000])
            txt.configure(state="disabled")

        lb.bind("<<ListboxSelect>>", on_sel)
        if items:
            lb.selection_set(0)
            lb.event_generate("<<ListboxSelect>>")

        tk.Button(top, text="Закрыть", command=top.destroy).pack(pady=4)
