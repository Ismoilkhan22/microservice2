# payment-service/alembic/env.py
# ============================================
# ALEMBIC MIGRATION SETUP
# ============================================


import sys
import os

# Project root-ni topish (env.py joyi: payment_service/app/migrations/env.py)
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../")
)
sys.path.append(BASE_DIR)
from shared.config import get_settings
from payment_service.app.database.base import Base
from payment_service.app.models.payment import Payment

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
config = context.config
fileConfig(config.config_file_name)

# Migration target metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Offline migration"""
    url = get_settings().DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online migration"""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_settings().DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.QueuePool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()