"""Добавление флага принудительной смены пароля.

Revision ID: 002_must_change_pwd
Revises: 001_initial
Create Date: 2026-05-01

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "002_must_change_pwd"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Колонка ``must_change_password`` у ``users`` (если ещё нет — после ``001`` из метаданных колонка уже может быть)."""

    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("users")}
    if "must_change_password" in cols:
        return
    op.add_column(
        "users",
        sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    """Удаляет колонку."""

    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("users")}
    if "must_change_password" not in cols:
        return
    op.drop_column("users", "must_change_password")
