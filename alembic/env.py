"""
alembic/env.py
--------------
Alembic's configuration file. This runs every time you use the 'alembic' CLI command.

Key features:
- Reads the DATABASE_URL from environment variables
- Imports all SQLAlchemy models so Alembic can detect schema changes
- Configured for async PostgreSQL connections
"""

import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import os
import sys

# Add the project root to Python path so we can import 'app'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import ALL models here so Alembic can detect them for autogenerate
from app.database import Base
from app.models import User, Article, Tag, Comment, Bookmark  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is what Alembic uses to generate migrations ('target_metadata')
target_metadata = Base.metadata


def get_url():
    """
    Read DATABASE_URL from environment. This allows different URLs for
    development, testing, and production without changing this file.
    """
    return os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/knowledge_base")


def run_migrations_offline() -> None:
    """
    Run migrations without a live database connection.
    Generates SQL scripts that can be reviewed and run manually.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async database connection (required for asyncpg)."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Don't pool connections for migrations
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for running migrations against a live database."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
