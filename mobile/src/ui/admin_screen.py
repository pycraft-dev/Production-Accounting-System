"""Смена пароля при первом входе."""

from __future__ import annotations

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner


def _next_login_for_role(users: list[dict], role: str) -> str:
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


class ForcePasswordScreen(MDScreen):
    """Обязательная смена пароля (до доступа к меню)."""

    def __init__(self, app, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app_ref = app
        self.name = "force_pwd"
        root = MDBoxLayout(orientation="vertical", padding=24, spacing=12)
        root.add_widget(MDLabel(text="Задайте новый пароль (не короче 8 символов)."))
        self.new1 = MDTextField(hint_text="Новый пароль", password=True, mode="rectangle")
        self.new2 = MDTextField(hint_text="Повтор пароля", password=True, mode="rectangle")
        root.add_widget(self.new1)
        root.add_widget(self.new2)
        self.err = MDLabel(text="", halign="left")
        root.add_widget(self.err)
        root.add_widget(MDRaisedButton(text="Сохранить", on_release=self._save))
        self.add_widget(root)

    def _save(self, *_args) -> None:
        cur = getattr(self.app_ref, "_temp_login_password", "") or ""
        a, b = self.new1.text, self.new2.text
        if len(a) < 8:
            self.err.text = "Минимум 8 символов"
            return
        if a != b:
            self.err.text = "Пароли не совпадают"
            return
        try:
            self.app_ref.api.change_password(cur, a)
        except Exception as e:
            self.err.text = str(e)
            return
        self.app_ref._temp_login_password = ""
        try:
            self.app_ref.profile = self.app_ref.api.me()
        except Exception:
            pass
        if getattr(self.app_ref, "_remember_login", False):
            from src.core import session_store

            session_store.save_session(
                self.app_ref.data_root,
                self.app_ref.api,
                getattr(self.app_ref, "_login_key_to_save", ""),
            )
        self.app_ref._remember_login = False
        self.app_ref.sm.current = "menu"


class AdminScreen(MDScreen):
    """Упрощённая админка: список пользователей и создание."""

    def __init__(self, app, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app_ref = app
        self.name = "admin"
        self._users_json: list[dict] = []
        root = MDBoxLayout(orientation="vertical", padding=12, spacing=8)
        self.list_label = MDLabel(text="", halign="left")
        scroll_container = MDBoxLayout(orientation="vertical", adaptive_height=True)
        self.list_body = scroll_container
        root.add_widget(self.list_label)
        root.add_widget(scroll_container)
        self.uid_field = MDTextField(hint_text="ID (для смены пароля/отключения)", mode="rectangle")
        root.add_widget(MDLabel(text="Роль нового пользователя:", halign="left"))
        self.role_spinner = Spinner(
            text="worker",
            values=("worker", "admin", "constructor"),
            size_hint_y=None,
            height=44,
        )
        self.role_spinner.bind(text=self._sync_login_suggestion)
        root.add_widget(self.role_spinner)
        self.login_field = MDTextField(hint_text="Логин (admin1, worker2…)", mode="rectangle")
        self.name_field = MDTextField(hint_text="ФИО", mode="rectangle")
        self.pwd_field = MDTextField(hint_text="Пароль (≥8)", password=True, mode="rectangle")
        root.add_widget(self.uid_field)
        root.add_widget(self.login_field)
        root.add_widget(self.name_field)
        root.add_widget(self.pwd_field)
        root.add_widget(MDRaisedButton(text="Обновить список", on_release=lambda *a: self.refresh()))
        root.add_widget(MDRaisedButton(text="Создать пользователя", on_release=self._create))
        root.add_widget(MDRaisedButton(text="Сменить пароль (по ID)", on_release=self._chpwd))
        root.add_widget(MDRaisedButton(text="Отключить (по ID)", on_release=self._deact))
        root.add_widget(MDRaisedButton(text="Документация (docs)", on_release=self._open_docs))
        root.add_widget(MDRaisedButton(text="Назад", on_release=lambda *a: setattr(app.sm, "current", "menu")))
        self.add_widget(root)

    def _sync_login_suggestion(self, *_args) -> None:
        role = self.role_spinner.text or "worker"
        self.login_field.text = _next_login_for_role(self._users_json, role)

    def on_pre_enter(self, *args) -> None:
        self.refresh()

    def refresh(self, *_a) -> None:
        r = self.app_ref.api.get("/api/admin/users")
        if not r.ok:
            self.list_label.text = f"Ошибка: {r.text[:200]}"
            return
        self._users_json = r.json()
        lines = []
        for u in self._users_json:
            lines.append(
                f"#{u['id']} {u.get('login', '')} ({u['role']}) {'активен' if u.get('is_active') else 'нет'}",
            )
        self.list_label.text = "\n".join(lines) if lines else "Нет пользователей"
        self._sync_login_suggestion()

    def _create(self, *_a) -> None:
        body = {
            "login": self.login_field.text.strip(),
            "full_name": self.name_field.text.strip(),
            "password": self.pwd_field.text,
            "role": self.role_spinner.text or "worker",
        }
        r = self.app_ref.api.post("/api/admin/users", json_body=body)
        if r.ok:
            self.app_ref.notify("Пользователь создан")
            self.refresh()
        else:
            self.app_ref.notify(f"Ошибка: {r.text[:180]}")

    def _chpwd(self, *_a) -> None:
        raw = self.uid_field.text.strip()
        if not raw.isdigit():
            self.app_ref.notify("Укажите ID")
            return
        new_p = self.pwd_field.text
        if len(new_p) < 8:
            self.app_ref.notify("Пароль от 8 символов")
            return
        r = self.app_ref.api.post(f"/api/admin/users/{raw}/change-password", json_body={"new_password": new_p})
        if r.ok:
            self.app_ref.notify("Пароль обновлён")
            self.refresh()
        else:
            self.app_ref.notify(f"Ошибка: {r.text[:180]}")

    def _deact(self, *_a) -> None:
        raw = self.uid_field.text.strip()
        if not raw.isdigit():
            self.app_ref.notify("Укажите ID")
            return
        r = self.app_ref.api.delete(f"/api/admin/users/{raw}")
        if r.ok:
            self.app_ref.notify("Учётная запись отключена")
            self.refresh()
        else:
            self.app_ref.notify(f"Ошибка: {r.text[:180]}")

    def _open_docs(self, *_a) -> None:
        """Markdown из каталога docs/ на сервере (только admin)."""

        r = self.app_ref.api.get("/api/admin/docs")
        if not r.ok:
            self.app_ref.notify("Список документов недоступен")
            return
        pairs = [(str(d["filename"]), str(d.get("title", d["filename"]))) for d in r.json()]
        pairs = [(fn, t) for fn, t in pairs if fn]
        if not pairs:
            self.app_ref.notify("На сервере нет .md в docs/")
            return
        layout = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
        titles = [p[1] for p in pairs]
        sp = Spinner(text=titles[0], values=titles, size_hint_y=None, height=dp(44))
        scroll = ScrollView()
        lbl = Label(
            text="",
            size_hint_y=None,
            halign="left",
            valign="top",
            padding=(dp(4), dp(4)),
        )

        def set_height(instance: Label, size: tuple[float, float]) -> None:
            instance.height = max(size[1], sp.height)

        lbl.bind(texture_size=set_height)

        def sync_text_size(*_args: object) -> None:
            lbl.text_size = (max(scroll.width - dp(16), 100), None)

        scroll.bind(width=sync_text_size)
        scroll.add_widget(lbl)

        def load_doc(*_args: object) -> None:
            idx = titles.index(sp.text)
            fn = pairs[idx][0]
            rr = self.app_ref.api.get(f"/api/admin/docs/{fn}")
            body = (rr.text if rr.ok else (rr.text or "Ошибка"))[:120_000]
            lbl.text = body or " "
            sync_text_size()

        layout.add_widget(sp)
        layout.add_widget(MDRaisedButton(text="Показать / обновить", on_release=load_doc))
        layout.add_widget(scroll)
        pop = Popup(title="Документация", content=layout, size_hint=(0.94, 0.9))
        pop.open()
        Clock.schedule_once(lambda _dt: load_doc(), 0.12)
