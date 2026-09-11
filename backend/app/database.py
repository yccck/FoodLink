from __future__ import annotations

from typing import Generator

from sqlalchemy import Engine, create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import DATA_DIR, settings


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str) -> Engine:
    options = {}
    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False, "timeout": 10}
        if database_url in ("sqlite://", "sqlite:///:memory:"):
            options["poolclass"] = StaticPool

    created_engine = create_engine(database_url, **options)

    if database_url.startswith("sqlite"):

        @event.listens_for(created_engine, "connect")
        def _set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=10000")
            cursor.close()

    return created_engine


DATA_DIR.mkdir(parents=True, exist_ok=True)
engine = build_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_database(bind: Engine = engine) -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=bind)
    _ensure_sqlite_compatibility_columns(bind)


def _ensure_sqlite_compatibility_columns(bind: Engine) -> None:
    """Add additive fields for local databases created before schema updates."""

    if bind.dialect.name != "sqlite":
        return
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    statements = []
    if "products" in tables:
        columns = {column["name"] for column in inspector.get_columns("products")}
        if "business_open_time" not in columns:
            statements.append(
                "ALTER TABLE products ADD COLUMN business_open_time VARCHAR(5) "
                "NOT NULL DEFAULT '08:00'"
            )
        if "business_close_time" not in columns:
            statements.append(
                "ALTER TABLE products ADD COLUMN business_close_time VARCHAR(5) "
                "NOT NULL DEFAULT '22:00'"
            )
    if "orders" in tables:
        columns = {column["name"] for column in inspector.get_columns("orders")}
        if "close_reason" not in columns:
            statements.append("ALTER TABLE orders ADD COLUMN close_reason VARCHAR(32)")
        if "closed_at" not in columns:
            statements.append("ALTER TABLE orders ADD COLUMN closed_at DATETIME")
    if statements:
        with bind.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
