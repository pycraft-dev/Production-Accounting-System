"""Заполнение демо-данными (admin / worker1 / constructor1)."""

from __future__ import annotations

import sys
from pathlib import Path

# Запуск: из каталога backend — ``python scripts\seed_data.py``
# Python добавляет в path папку ``scripts``, а не корень backend — исправляем:
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from faker import Faker
from sqlalchemy import select

from app.core.security import hash_password
from app.db.database import Base, get_engine, get_session_factory
from app.models.defect import Defect, DefectCategory, DefectPriority, DefectStatus
from app.models.equipment import Equipment
from app.models.project import Project
from app.models.user import User, UserRole


def main() -> None:
    """Создаёт таблицы (если нужно) и демо-пользователей."""

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    factory = get_session_factory()
    fake = Faker("ru_RU")
    with factory() as db:
        if db.scalar(select(User).where(User.email == "admin")):
            print("Демо-данные уже загружены, пропуск.")
            return
        users = [
            User(
                email="admin",
                full_name="Администратор",
                hashed_password=hash_password("admin"),
                role=UserRole.admin,
                must_change_password=True,
            ),
            User(
                email="worker1",
                full_name="Иванов И.И.",
                hashed_password=hash_password("worker12345"),
                role=UserRole.worker,
                must_change_password=False,
            ),
            User(
                email="constructor1",
                full_name="Петров П.П.",
                hashed_password=hash_password("constructor12345"),
                role=UserRole.constructor,
                must_change_password=False,
            ),
        ]
        for u in users:
            db.add(u)
        db.flush()
        proj = Project(name="Демо-изделие", code="DEMO-001", description=fake.text(120))
        db.add(proj)
        db.flush()
        eq = Equipment(name="Станок 1", workshop="Цех 1", ideal_cycle_seconds=60.0)
        db.add(eq)
        db.flush()
        w = next(u for u in users if u.role == UserRole.worker)
        d = Defect(
            description=fake.text(200),
            workshop="Барнаул",
            status=DefectStatus.new,
            priority=DefectPriority.medium,
            category=DefectCategory.production,
            created_by_id=w.id,
            project_id=proj.id,
        )
        db.add(d)
        db.commit()
        print("Готово: admin / admin, worker1 / worker12345, constructor1 / constructor12345")


if __name__ == "__main__":
    main()
