"""Экран создания брака."""

from __future__ import annotations

import os
import re
import subprocess
import threading
import time
from pathlib import Path

from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.utils import platform as kivy_platform
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, TwoLineListItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField

# Синхронно с backend/app/constants.py — DEFECT_WORKSHOP_CHOICES
_WORKSHOPS_FALLBACK = ("Барнаул", "Павловск")

_STATUS_RU = {
    "new": "новая",
    "in_progress": "в работе",
    "resolved": "закрыта",
    "rejected": "отклонена",
}


def _iso_dt(s: str | None) -> str:
    if not s:
        return "—"
    # 2025-01-15T12:30:45+00:00 → коротко
    s = re.sub(r"([.+-]\d{2}:\d{2}|Z)$", "", str(s).replace("T", " "))
    return s[:16] if len(s) >= 16 else s


def _open_path_cross_platform(path: str) -> None:
    """Открывает локальный файл в просмотрщике ОС (фото/видео и т.д.)."""

    p = kivy_platform
    if p == "win":
        os.startfile(path)  # type: ignore[attr-defined]
        return
    if p == "macosx":
        subprocess.Popen(["open", path])
        return
    if p == "android":
        _android_intent_view_file(path)
        return
    subprocess.Popen(["xdg-open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _android_intent_view_file(path: str) -> None:
    """Просмотр файла через внешнее приложение (p4a / jnius)."""

    import mimetypes

    from jnius import autoclass

    Intent = autoclass("android.content.Intent")
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Uri = autoclass("android.net.Uri")
    File = autoclass("java.io.File")

    activity = PythonActivity.mActivity
    file_obj = File(path)
    uri = Uri.fromFile(file_obj)
    mime, _ = mimetypes.guess_type(path)
    intent = Intent(Intent.ACTION_VIEW)
    intent.setDataAndType(uri, mime or "*/*")
    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    activity.startActivity(intent)


class DefectScreen(MDScreen):
    """Форма брака: мои заявки (интерактивный список), цех, описание, вложения."""

    def __init__(self, app, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app_ref = app
        self.name = "defect"
        self._workshops = list(_WORKSHOPS_FALLBACK)
        self._media_paths: list[str] = []

        outer = MDBoxLayout(orientation="vertical", padding=16, spacing=8)
        outer.add_widget(MDLabel(text="Мои заявки", halign="left", theme_text_color="Primary"))

        row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=8, adaptive_height=False)
        row.add_widget(
            MDRaisedButton(
                text="Обновить список",
                on_release=lambda *a: self.refresh_my_defects(),
                size_hint_x=0.5,
            ),
        )
        outer.add_widget(row)

        self._list_hint = MDLabel(
            text="Загрузка…",
            halign="left",
            theme_text_color="Secondary",
            size_hint_y=None,
        )
        outer.add_widget(self._list_hint)

        self.defect_list_scroll = MDScrollView(size_hint_y=None, height=dp(220), do_scroll_x=False)
        self.defect_list = MDList()
        self.defect_list_scroll.add_widget(self.defect_list)
        outer.add_widget(self.defect_list_scroll)

        outer.add_widget(MDLabel(text="Новая заявка", halign="left", theme_text_color="Primary"))
        outer.add_widget(MDLabel(text="Цех", halign="left"))
        self.workshop_spinner = Spinner(
            text=self._workshops[0],
            values=self._workshops,
            size_hint_y=None,
            height=44,
        )
        outer.add_widget(self.workshop_spinner)
        self.desc = MDTextField(hint_text="Описание", multiline=True, mode="rectangle")
        outer.add_widget(self.desc)
        self.media_lbl = MDLabel(text="Вложения: нет", halign="left")
        outer.add_widget(self.media_lbl)

        media_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(52), spacing=dp(8))
        media_row.add_widget(
            MDRaisedButton(
                text="Прикрепить файл",
                on_release=self._pick_media,
                size_hint_x=1,
            ),
        )
        if kivy_platform == "android":
            media_row.add_widget(
                MDRaisedButton(
                    text="Снять фото",
                    on_release=self._camera_take_photo,
                    size_hint_x=1,
                ),
            )
            media_row.add_widget(
                MDRaisedButton(
                    text="Видео",
                    on_release=self._camera_take_video,
                    size_hint_x=1,
                ),
            )
        outer.add_widget(media_row)

        outer.add_widget(MDRaisedButton(text="Отправить", on_release=self._send))
        self.add_widget(outer)

    def on_pre_enter(self, *args) -> None:
        self._fetch_workshops()
        self.refresh_my_defects()

    def _fetch_workshops(self) -> None:
        try:
            r = self.app_ref.api.get("/api/defects/workshops")
            if r.ok:
                data = r.json()
                if isinstance(data, list) and data:
                    self._workshops = data
                    self.workshop_spinner.values = self._workshops
                    if self.workshop_spinner.text not in self._workshops:
                        self.workshop_spinner.text = self._workshops[0]
        except Exception:
            pass

    def refresh_my_defects(self, *_a) -> None:
        def worker() -> None:
            err: str | None = None
            items: list[dict] = []
            try:
                rr = self.app_ref.api.get("/api/defects", params={"mine": "true", "limit": 80})
                if not rr.ok:
                    err = rr.text[:400]
                else:
                    items = rr.json()
                    if not isinstance(items, list):
                        err = "Неверный ответ сервера"
                        items = []
            except Exception as e:
                err = str(e)[:400]

            def apply_ui(dt: float) -> None:
                self._apply_defect_list(items, err)

            Clock.schedule_once(apply_ui, 0)

        self._list_hint.text = "Загрузка…"
        threading.Thread(target=worker, daemon=True).start()

    def _apply_defect_list(self, items: list[dict], err: str | None) -> None:
        self.defect_list.clear_widgets()
        if err:
            self._list_hint.text = f"Список недоступен: {err}"
            return
        if not items:
            self._list_hint.text = "Пока нет отправленных заявок — они появятся здесь после «Отправить»."
            return
        self._list_hint.text = f"Всего: {len(items)} (нажмите строку для подробностей)"
        for d in items:
            if not isinstance(d, dict) or "id" not in d:
                continue
            did = int(d["id"])
            st_raw = str(d.get("status", ""))
            st = _STATUS_RU.get(st_raw, st_raw)
            desc = str(d.get("description", "")).strip()
            tw = TwoLineListItem(
                text=f"#{did} · {d.get('workshop', '')} · {st}",
                secondary_text=desc[:200] + ("…" if len(desc) > 200 else ""),
            )
            tw.bind(on_release=lambda _inst, i=did: self._open_detail(i))
            self.defect_list.add_widget(tw)

    def _open_detail(self, defect_id: int) -> None:
        def worker() -> None:
            detail_err: str | None = None
            data: dict | None = None
            try:
                rr = self.app_ref.api.get(f"/api/defects/{defect_id}")
                if not rr.ok:
                    detail_err = rr.text[:800]
                else:
                    data = rr.json()
            except Exception as e:
                detail_err = str(e)[:400]

            def show(dt: float) -> None:
                if detail_err or not isinstance(data, dict):
                    self.app_ref.notify("Не удалось открыть заявку")
                    return
                st_raw = str(data.get("status", ""))
                st = _STATUS_RU.get(st_raw, st_raw)

                # Корень: сверху гибкая прокрутка (заголовок + описание), снизу фиксированный блок с кнопками
                root_lay = MDBoxLayout(
                    orientation="vertical",
                    padding=dp(18),
                    spacing=dp(8),
                    size_hint=(1, 1),
                )

                mid_scroll = MDScrollView(
                    size_hint_y=1,
                    size_hint_x=1,
                    do_scroll_x=False,
                    bar_width=dp(10),
                )
                mid_inner = MDBoxLayout(
                    orientation="vertical",
                    adaptive_height=True,
                    size_hint_y=None,
                    spacing=dp(12),
                )
                mid_scroll.add_widget(mid_inner)

                mid_inner.add_widget(
                    MDLabel(
                        text=f"Заявка №{data.get('id')}",
                        font_style="H5",
                        bold=True,
                        halign="left",
                        theme_text_color="Custom",
                        text_color=[0.55, 0.92, 0.85, 1],
                        size_hint_y=None,
                        height=dp(42),
                    ),
                )
                meta_txt = (
                    f"[b][color=#9ca3af]Цех[/color][/b]  {data.get('workshop')}\n"
                    f"[b][color=#9ca3af]Статус[/color][/b]  {st}\n"
                    f"[b][color=#9ca3af]Создана[/color][/b]  {_iso_dt(str(data.get('created_at')))}"
                )
                mid_inner.add_widget(
                    MDLabel(
                        text=meta_txt,
                        markup=True,
                        halign="left",
                        font_size=sp(16),
                        size_hint_y=None,
                        adaptive_height=True,
                    ),
                )
                mid_inner.add_widget(
                    MDLabel(
                        text="Описание",
                        halign="left",
                        theme_text_color="Secondary",
                        font_size=sp(14),
                        bold=True,
                        size_hint_y=None,
                        height=dp(28),
                    ),
                )
                desc_lbl = MDLabel(
                    text=str(data.get("description", "")),
                    halign="left",
                    valign="top",
                    font_size=sp(17),
                    size_hint_y=None,
                    adaptive_height=True,
                )

                def sync_desc_w(*_a: object) -> None:
                    desc_lbl.text_size = (max(mid_scroll.width - dp(28), 80), None)

                mid_scroll.bind(width=sync_desc_w)
                mid_inner.add_widget(desc_lbl)

                raw_ids = data.get("attachment_file_ids") or []
                fids: list[int] = []
                for x in raw_ids:
                    try:
                        fids.append(int(x))
                    except (TypeError, ValueError):
                        continue

                footer = MDBoxLayout(
                    orientation="vertical",
                    adaptive_height=True,
                    size_hint_y=None,
                    spacing=dp(8),
                    padding=(0, dp(10), 0, 0),
                )

                footer.add_widget(
                    MDLabel(
                        text="Вложения",
                        halign="left",
                        theme_text_color="Secondary",
                        font_size=sp(14),
                        bold=True,
                        size_hint_y=None,
                        height=dp(28),
                    ),
                )
                if fids:
                    footer.add_widget(
                        MDLabel(
                            text="Нажмите — скачать и открыть в галерее / плеере",
                            halign="left",
                            theme_text_color="Hint",
                            font_size=sp(13),
                            size_hint_y=None,
                            adaptive_height=True,
                        ),
                    )
                    for idx, fid in enumerate(fids, 1):
                        btn = MDRaisedButton(
                            text=f"   📎  Вложение {idx}  —  открыть файл   ",
                            size_hint_y=None,
                            height=dp(52),
                            font_size=sp(16),
                        )
                        btn.bind(on_release=lambda inst, f=fid: self._download_and_open_attachment(f))
                        footer.add_widget(btn)
                else:
                    footer.add_widget(
                        MDLabel(
                            text="Файлов нет",
                            halign="left",
                            theme_text_color="Hint",
                            font_size=sp(15),
                            size_hint_y=None,
                            height=dp(32),
                        ),
                    )

                pop = Popup(
                    title=f"Брак #{defect_id}",
                    content=root_lay,
                    size_hint=(0.95, 0.88),
                    auto_dismiss=True,
                    title_size=sp(20),
                    title_color=[0.88, 0.97, 0.94, 1],
                    separator_color=[0.0, 0.7, 0.62, 1],
                    separator_height=dp(2),
                    background_color=[0.12, 0.12, 0.14, 0.97],
                )
                close_btn = MDRaisedButton(
                    text="Закрыть",
                    size_hint_y=None,
                    height=dp(50),
                    font_size=sp(15),
                )
                close_btn.bind(on_release=lambda *a: pop.dismiss())
                footer.add_widget(close_btn)

                root_lay.add_widget(mid_scroll)
                root_lay.add_widget(footer)
                pop.open()
                Clock.schedule_once(lambda _dt: sync_desc_w(), 0)

            Clock.schedule_once(show, 0)

        threading.Thread(target=worker, daemon=True).start()

    def _download_and_open_attachment(self, file_id: int) -> None:
        """Скачивает файл с сервера и открывает во внешнем приложении."""

        app = self.app_ref

        def work() -> None:
            err: str | None = None
            out_path: str | None = None
            try:
                cache_root = Path(app.data_root) / "defect_attach_cache"
                cache_root.mkdir(parents=True, exist_ok=True)
                data, name = app.api.download_file(file_id)
                ext = Path(name or "").suffix or ".bin"
                dest = cache_root / f"att_{file_id}{ext}"
                dest.write_bytes(data)
                out_path = str(dest.resolve())
            except Exception as e:
                err = str(e)[:240]

            def ui(_dt: float) -> None:
                if err:
                    app.notify(err)
                    return
                if not out_path:
                    return
                try:
                    _open_path_cross_platform(out_path)
                except Exception as e2:
                    app.notify(f"Сохранено: {out_path}\nОткройте вручную. ({e2})")

            Clock.schedule_once(ui, 0)

        threading.Thread(target=work, daemon=True).start()

    def _set_paths(self, paths: list[str]) -> None:
        self._media_paths = paths
        self.media_lbl.text = f"Вложения: {len(paths)} файл(ов)" if paths else "Вложения: нет"

    def _append_media_path(self, path: str) -> None:
        """Добавить один файл к списку вложений (камера, после съёмки)."""

        p = (path or "").strip()
        if not p or not Path(p).is_file():
            return
        if p not in self._media_paths:
            self._media_paths.append(p)
            self.media_lbl.text = f"Вложения: {len(self._media_paths)} файл(ов)"

    def _camera_capture_dir(self) -> Path:
        d = Path(self.app_ref.data_root) / "camera_captures"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _camera_take_photo(self, *_a) -> None:
        if kivy_platform != "android":
            self.app_ref.notify("Съёмка с камеры — в Android-приложении")
            return
        try:
            from plyer import camera as plyer_camera
        except Exception as e:
            self.app_ref.notify(str(e)[:200])
            return

        out = str(self._camera_capture_dir() / f"defect_{int(time.time() * 1000)}.jpg")

        def on_done(filepath: str) -> bool:
            def ui(_dt: float) -> None:
                if filepath and Path(filepath).is_file():
                    self._append_media_path(filepath)
                    self.app_ref.notify("Фото добавлено к вложениям")
                else:
                    self.app_ref.notify("Фото не сохранено (отмена или ошибка камеры)")

            Clock.schedule_once(ui, 0)
            return False

        try:
            plyer_camera.take_picture(filename=out, on_complete=on_done)
        except NotImplementedError:
            self.app_ref.notify("Камера не поддерживается на этой платформе")
        except Exception as e:
            self.app_ref.notify(str(e)[:220])

    def _camera_take_video(self, *_a) -> None:
        if kivy_platform != "android":
            self.app_ref.notify("Запись видео — в Android-приложении")
            return
        try:
            from plyer import camera as plyer_camera
        except Exception as e:
            self.app_ref.notify(str(e)[:200])
            return

        out = str(self._camera_capture_dir() / f"defect_{int(time.time() * 1000)}.mp4")

        def on_done(filepath: str) -> bool:
            def ui(_dt: float) -> None:
                if filepath and Path(filepath).is_file():
                    self._append_media_path(filepath)
                    self.app_ref.notify("Видео добавлено к вложениям")
                else:
                    self.app_ref.notify("Видео не сохранено (отмена или ошибка)")

            Clock.schedule_once(ui, 0)
            return False

        try:
            plyer_camera.take_video(filename=out, on_complete=on_done)
        except NotImplementedError:
            self.app_ref.notify("Видеокамера не поддерживается")
        except Exception as e:
            self.app_ref.notify(str(e)[:220])

    def _pick_media_tk(self) -> None:
        try:
            from tkinter import Tk, filedialog

            root = Tk()
            root.withdraw()
            paths = filedialog.askopenfilenames(
                title="Фото или видео",
                filetypes=[
                    ("Медиа", "*.jpg *.jpeg *.png *.webp *.mp4 *.webm *.mov"),
                    ("Все", "*.*"),
                ],
            )
            root.destroy()
            if paths:
                Clock.schedule_once(lambda dt: self._set_paths(list(paths)), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.app_ref.notify(str(e)), 0)

    def _pick_media(self, *a) -> None:
        if kivy_platform == "android":
            try:
                from plyer import filechooser

                def on_sel(sel: list | None) -> None:
                    paths = list(sel) if sel else []
                    Clock.schedule_once(lambda dt, p=paths: self._set_paths(p), 0)

                filechooser.open_file(
                    on_selection=on_sel,
                    filters=[
                        [
                            "media",
                            "*.jpg",
                            "*.jpeg",
                            "*.png",
                            "*.webp",
                            "*.mp4",
                            "*.webm",
                            "*.mov",
                        ]
                    ],
                )
            except Exception as e:
                self.app_ref.notify(str(e))
        else:
            threading.Thread(target=self._pick_media_tk, daemon=True).start()

    def _send(self, *a) -> None:
        desc = (self.desc.text or "").strip()
        if not desc:
            self.app_ref.notify("Укажите описание")
            return
        workshop = self.workshop_spinner.text or self._workshops[0]
        payload = {
            "description": desc,
            "workshop": workshop,
            "priority": "medium",
            "category": "production",
        }
        try:
            r = self.app_ref.api.post("/api/defects", json_body=payload, offline_fallback=True)
            r.raise_for_status()
            did = r.json()["id"]
            for p in self._media_paths:
                try:
                    pr = self.app_ref.api.post_defect_media(f"/api/defects/{did}/photos", p)
                    if not pr.ok:
                        self.app_ref.notify(f"{Path(p).name}: не загружен")
                except Exception:
                    self.app_ref.notify(f"{Path(p).name}: ошибка отправки")
            self._media_paths = []
            self.media_lbl.text = "Вложения: нет"
            self.desc.text = ""
            self.app_ref.notify("Брак отправлен")
            self.refresh_my_defects()
        except Exception:
            self.app_ref.notify("Сохранено в оффлайн-очередь")
