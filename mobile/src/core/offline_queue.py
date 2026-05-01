"""Очередь оффлайн-запросов (до 100 записей)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class QueueItemState(str, Enum):
    """Состояние записи в очереди."""

    pending = "pending"
    sent = "sent"


@dataclass
class QueuedAction:
    """Действие для повторной отправки."""

    id: int
    method: str
    path: str
    body: dict | None


class OfflineQueue:
    """FIFO-очередь с ограничением размера."""

    max_items = 100

    def __init__(self, db_path: str | Path) -> None:
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.path))

    def _init_db(self) -> None:
        with self._conn() as c:
            c.execute(
                """CREATE TABLE IF NOT EXISTS queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    method TEXT NOT NULL,
                    path TEXT NOT NULL,
                    body TEXT,
                    state TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )"""
            )

    def enqueue(self, method: str, path: str, body: dict | None = None) -> None:
        """Добавляет запись (отбрасывает старые при переполнении)."""

        with self._conn() as c:
            cnt = c.execute("SELECT COUNT(*) FROM queue WHERE state='pending'").fetchone()[0]
            if cnt >= self.max_items:
                raise RuntimeError("Очередь оффлайна переполнена (макс. 100)")
            c.execute(
                "INSERT INTO queue (method, path, body) VALUES (?, ?, ?)",
                (method, path, json.dumps(body) if body is not None else None),
            )

    def pending(self) -> list[QueuedAction]:
        """Возвращает ожидающие отправки записи."""

        with self._conn() as c:
            rows = c.execute(
                "SELECT id, method, path, body FROM queue WHERE state='pending' ORDER BY id"
            ).fetchall()
        out: list[QueuedAction] = []
        for r in rows:
            body = json.loads(r[3]) if r[3] else None
            out.append(QueuedAction(id=r[0], method=r[1], path=r[2], body=body))
        return out

    def mark_sent(self, item_id: int) -> None:
        """Помечает запись как отправленную."""

        with self._conn() as c:
            c.execute("UPDATE queue SET state='sent' WHERE id=?", (item_id,))
