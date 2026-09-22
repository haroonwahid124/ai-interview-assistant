"""
Database setup with SQLAlchemy 2.0.

`get_db` is a FastAPI dependency: each request gets its own session,
and the session is always closed when the request finishes.
"""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def normalise_database_url(url: str) -> str:
    """Hosted Postgres providers hand out postgres:// URLs; SQLAlchemy + psycopg 3
    needs postgresql+psycopg://."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


DATABASE_URL = normalise_database_url(settings.database_url)

# SQLite refuses to share a connection across threads unless told otherwise;
# FastAPI runs sync endpoints in a thread pool, so we switch that check off.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
