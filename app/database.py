"""Database configuration and SQLAlchemy session dependency."""

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./classsignal.db")


class Base(DeclarativeBase):
    """Base class shared by all SQLAlchemy models."""


def make_engine(database_url: str) -> Engine:
    """Create an engine, enabling SQLite foreign-key checks when applicable."""
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine_options = {"connect_args": connect_args}
    if database_url in {"sqlite://", "sqlite:///:memory:"}:
        engine_options["poolclass"] = StaticPool
    database_engine = create_engine(database_url, **engine_options)

    if database_url.startswith("sqlite"):

        @event.listens_for(database_engine, "connect")
        def enable_sqlite_foreign_keys(connection, _record) -> None:
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return database_engine


engine = make_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Provide one database session per request and always close it."""
    with SessionLocal() as session:
        yield session
