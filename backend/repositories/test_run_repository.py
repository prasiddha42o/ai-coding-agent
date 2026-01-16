"""Data-access layer for TestRun — thin query wrappers, no business logic."""
import uuid

from sqlalchemy.orm import Session

from backend.models.test_run import TestRun


def list_by_session(db: Session, session_id: uuid.UUID) -> list[TestRun]:
    return (
        db.query(TestRun)
        .filter(TestRun.session_id == session_id)
        .order_by(TestRun.created_at.desc())
        .all()
    )
