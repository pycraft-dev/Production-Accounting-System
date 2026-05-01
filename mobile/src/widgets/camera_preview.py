"""Заглушка предпросмотра камеры (plyer на устройстве)."""

from __future__ import annotations

from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen


class CameraPreviewScreen(MDScreen):
    """На устройстве подключите plyer.camera; здесь — текстовая подсказка."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.name = "camera"
        self.add_widget(
            MDLabel(
                text="Камера: используйте системный модуль или plyer в сборке APK",
                halign="center",
            )
        )
