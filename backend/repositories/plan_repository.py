"""Data-access layer for Plan — thin query wrappers, no business logic."""
import uuid

from sqlalchemy.orm import Session

from backend.models.plan import Plan


def get_by_id(db: Session, plan_id: uuid.UUID) -> Plan | None:
    return db.get(Plan, plan_id)


def list_by_session(db: Session, session_id: uuid.UUID) -> list[Plan]:
    return (
        db.query(Plan)
        .filter(Plan.session_id == session_id)
        .order_by(Plan.created_at.desc())
        .all()
    )
