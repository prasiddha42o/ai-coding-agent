"""SQLAlchemy engine, session factory, and declarative base."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    # pool_pre_ping: cheap SELECT 1 before reusing a pooled connection —
    # catches connections a remote Postgres (Neon, etc.) has already
    # dropped server-side, which a plain idle pool wouldn't notice until
    # the query that actually needed it failed.
    pool_pre_ping=True,
    # Recycle pooled connections every 5 minutes rather than holding them
    # indefinitely — serverless Postgres providers commonly close idle
    # server-side connections well under typical pool lifetimes, and
    # proactive recycling avoids depending on pre_ping to catch every case.
    pool_recycle=300,
    connect_args={"connect_timeout": 10},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
