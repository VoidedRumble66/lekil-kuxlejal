"""Migraciones por CLI y por la conexión transaccional del inicio de FastAPI."""

from alembic import context
from sqlmodel import SQLModel

from app import models  # noqa: F401: registra metadatos para autogeneración
from app.database import build_engine, resolve_database_url, migration_connection

config = context.config
target_metadata = SQLModel.metadata


def run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(
        url=resolve_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    connection = config.attributes.get("connection")
    if connection is not None:
        run_migrations(connection)
    else:
        engine = build_engine()
        with migration_connection(engine) as connection:
            run_migrations(connection)
        engine.dispose()
