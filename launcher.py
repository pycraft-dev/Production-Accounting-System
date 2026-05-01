#!/usr/bin/env python3
"""Графический лаунчер: API, десктоп и мобильный клиент (отдельные окна консоли)."""

from __future__ import annotations

import os
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _spawn_bat(
    name: str,
    procs: list[subprocess.Popen],
    extra_env: dict[str, str] | None = None,
) -> bool:
    """Новое окно cmd. Процесс сохраняется в procs — при закрытии лаунчера завершится вместе с дочерними (uvicorn и т.д.)."""

    bat = (ROOT / name).resolve()
    if not bat.is_file():
        return False
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    creationflags = subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    p = subprocess.Popen(
        ["cmd.exe", "/k", "call", str(bat)],
        cwd=str(ROOT),
        env=env,
        creationflags=creationflags,
        shell=False,
    )
    procs.append(p)
    return True


def _kill_spawned_consoles(procs: list[subprocess.Popen]) -> None:
    """Закрывает окна cmd, запущенные из лаунчера, и их дерево процессов (Python/uvicorn)."""

    no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    for p in list(procs):
        if p.poll() is not None:
            continue
        try:
            if sys.platform == "win32" and p.pid:
                subprocess.run(
                    ["taskkill", "/PID", str(p.pid), "/T", "/F"],
                    capture_output=True,
                    timeout=30,
                    creationflags=no_window,
                    check=False,
                )
            else:
                p.terminate()
                try:
                    p.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    p.kill()
        except Exception:
            pass
    procs.clear()


def _main() -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox
    except ImportError:
        if sys.platform == "win32":
            import ctypes

            ctypes.windll.user32.MessageBoxW(
                0,
                "Нужен Python с модулем tkinter (стандартная установка с python.org).",
                "Учёт производства — лаунчер",
                0x10,
            )
        else:
            print("Нужен Python с модулем tkinter.")
        sys.exit(1)

    child_procs: list[subprocess.Popen] = []

    win = tk.Tk()
    win.title("Учёт производства — лаунчер")
    win.minsize(380, 300)
    win.resizable(True, False)

    pad = {"padx": 14, "pady": 6}
    tk.Label(
        win,
        text=(
            "Запуск компонентов в отдельных окнах cmd.\n"
            "Сначала поднимите API, затем клиент.\n"
            "При закрытии лаунчера эти консоли будут завершены (вместе с сервером и клиентами)."
        ),
        justify="left",
    ).pack(anchor="w", **pad)

    api_url = tk.StringVar(value="http://127.0.0.1:8000")

    def start_api() -> None:
        if not _spawn_bat("start_server.bat", child_procs):
            messagebox.showerror("Лаунчер", f"Не найден: {ROOT / 'start_server.bat'}")

    def start_desktop() -> None:
        url = api_url.get().strip() or "http://127.0.0.1:8000"
        if not _spawn_bat("start_desktop.bat", child_procs, {"API_BASE_URL": url}):
            messagebox.showerror("Лаунчер", f"Не найден: {ROOT / 'start_desktop.bat'}")

    def start_mobile() -> None:
        url = api_url.get().strip() or "http://127.0.0.1:8000"
        if not _spawn_bat("start_mobile.bat", child_procs, {"API_BASE_URL": url}):
            messagebox.showerror("Лаунчер", f"Не найден: {ROOT / 'start_mobile.bat'}")

    def open_docs() -> None:
        webbrowser.open(api_url.get().strip().rstrip("/") + "/docs")

    def open_root() -> None:
        webbrowser.open(api_url.get().strip().rstrip("/"))

    def on_close() -> None:
        _kill_spawned_consoles(child_procs)
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)

    frm = tk.Frame(win)
    frm.pack(fill="x", **pad)
    tk.Label(frm, text="Базовый URL API (для клиентов):").pack(anchor="w")
    tk.Entry(frm, textvariable=api_url, width=48).pack(fill="x", pady=(4, 10))

    tk.Button(frm, text="1. Запустить сервер (API, порт 8000)", command=start_api, width=44).pack(
        fill="x", pady=3
    )
    tk.Button(frm, text="2. Десктоп-клиент (CustomTkinter)", command=start_desktop, width=44).pack(
        fill="x", pady=3
    )
    tk.Button(frm, text="3. Мобильный клиент на ПК (KivyMD)", command=start_mobile, width=44).pack(
        fill="x", pady=3
    )

    row = tk.Frame(win)
    row.pack(fill="x", **pad)
    tk.Button(row, text="Открыть /docs", command=open_docs).pack(side="left", padx=(0, 8))
    tk.Button(row, text="Открыть корень API", command=open_root).pack(side="left")

    tk.Label(
        win,
        text=f"Каталог проекта:\n{ROOT}",
        justify="left",
        fg="#555",
        font=("Segoe UI", 8),
    ).pack(anchor="w", padx=14, pady=(8, 4))

    win.mainloop()


if __name__ == "__main__":
    _main()
