"""
Создаёт первого администратора с логином ``admin`` и паролем ``admin``.

Если пользователь уже есть — скрипт ничего не меняет.
Запуск из каталога ``backend``: ``python scripts/create_first_admin.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.database import Base, get_engine, get_session_factory
from app.models.user import User, UserRole


def main() -> None:
    """Создаёт таблицы при необходимости и одного admin."""

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    factory = get_session_factory()
    with factory() as db:
        if db.scalar(select(User).where(User.email == "admin")):
            print("Администратор admin уже существует.")
            return
        db.add(
            User(
                email="admin",
                full_name="Администратор",
                hashed_password=hash_password("admin"),
                role=UserRole.admin,
                must_change_password=True,
            )
        )
        db.commit()
    print("Готово. Логин: admin, пароль: admin")


if __name__ == "__main__":
    main()
