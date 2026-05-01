"""Начальная схема БД.

Revision ID: 001_initial
Revises:
Create Date: 2026-05-01

"""

from alembic import op

from app.db.database import Base

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Создаёт все таблицы по метаданным SQLAlchemy."""

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    """Удаляет все таблицы приложения."""

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
