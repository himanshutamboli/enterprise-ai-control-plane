"""Database engine/session plumbing (SQLAlchemy 2.0).

Portable across SQLite (default, zero-infra) and PostgreSQL (production, via ``database_url``).
Schema is created with ``create_all`` for now; Alembic migrations land before the schema churns
(tracked in ROADMAP).
"""

from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def make_engine(url: str) -> Engine:
    connect_args: dict = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False  # FastAPI uses threads
        path = url.removeprefix("sqlite:///")
        if path and path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(url, connect_args=connect_args)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def init_db(engine: Engine) -> None:
    from control_plane.core import models  # noqa: F401 — register mappers before create_all

    Base.metadata.create_all(engine)
