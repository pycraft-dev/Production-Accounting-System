"""Alembic environment."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.db.database import Base
from app.models import (  # noqa: F401
    AuditLog,
    DailyReport,
    Defect,
    DefectAttachment,
    DefectComment,
    DefectStatusHistory,
    DowntimeRecord,
    Equipment,
    ErpEntityLink,
    ErpSyncRecord,
    Project,
    SchemeApprovalHistory,
    SchemeChange,
    StoredFile,
    User,
)

config = context.config
if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """URL БД из настроек приложения."""

    return get_settings().database_url


def run_migrations_offline() -> None:
    """Offline migrations."""

    url = get_url()
    if url.startswith("postgresql+psycopg2"):
        url = url.replace("postgresql+psycopg2", "postgresql")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online migrations."""

    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
