"""SQLite y migraciones; ninguna tabla operativa contiene datos de ejemplo."""

from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from sqlalchemy import DateTime, Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.types import TypeDecorator

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = BACKEND_DIR / "data" / "lekil.db"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator[datetime]):
    """SQLite guarda UTC; al leer siempre se reconstruye la zona explícita."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("La fecha debe incluir zona horaria.")
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)


def resolve_database_url(database_url: str | None = None) -> str:
    value = database_url or os.environ.get("DATABASE_URL")
    if not value:
        value = f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"
    url = make_url(value)
    if url.drivername != "sqlite":
        raise ValueError("La Fase 1 admite únicamente SQLite local (sqlite:///...).")
    if not url.database or url.database == ":memory:":
        raise ValueError("Se requiere un archivo SQLite persistente.")
    database_path = Path(url.database)
    if not database_path.is_absolute():
        database_path = BACKEND_DIR / database_path
    return url.set(database=str(database_path.resolve())).render_as_string(hide_password=False)


def build_engine(database_url: str | None = None) -> Engine:
    url = resolve_database_url(database_url)
    database_path = Path(make_url(url).database or "")
    database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 10})

    @event.listens_for(engine, "connect")
    def configure_sqlite(connection: Any, connection_record: Any) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=10000")
        cursor.close()

    return engine


@contextmanager
def migration_connection(engine: Engine):
    """Batch de SQLite con FK verificadas antes de confirmar, sólo al migrar."""
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.commit()
        try:
            with connection.begin():
                # Transacción física también para DDL en sqlite3 legacy mode.
                connection.exec_driver_sql("BEGIN IMMEDIATE")
                yield connection
                if connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall():
                    raise RuntimeError("La migración violaría la integridad referencial.")
        finally:
            connection.rollback()
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            connection.commit()


def migrate_database(engine: Engine) -> None:
    """Aplica migraciones versionadas antes de admitir solicitudes."""
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    with migration_connection(engine) as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
