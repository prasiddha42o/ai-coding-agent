"""Data-access layer for CodingSession — thin query wrappers, no business logic."""
import uuid

from sqlalchemy.orm import Session

from backend.models.session import CodingSession


def get_by_id(db: Session, session_id: uuid.UUID) -> CodingSession | None:
    return db.get(CodingSession, session_id)


def list_by_repository(db: Session, repository_id: uuid.UUID) -> list[CodingSession]:
    return (
        db.query(CodingSession)
        .filter(CodingSession.repository_id == repository_id)
        .order_by(CodingSession.created_at.desc())
        .all()
    )


def create(db: Session, **fields) -> CodingSession:
    session = CodingSession(**fields)
    db.add(session)
    db.flush()
    return session
