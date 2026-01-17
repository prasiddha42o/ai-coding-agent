"""Data-access layer for Commit — thin query wrappers, no business logic."""
import uuid

from sqlalchemy.orm import Session

from backend.models.commit import Commit


def list_by_session(db: Session, session_id: uuid.UUID) -> list[Commit]:
    return (
        db.query(Commit)
        .filter(Commit.session_id == session_id)
        .order_by(Commit.created_at.desc())
        .all()
    )
