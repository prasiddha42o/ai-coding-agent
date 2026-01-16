"""Data-access layer for Change — thin query wrappers, no business logic."""
import uuid

from sqlalchemy.orm import Session

from backend.models.change import Change


def list_by_plan(db: Session, plan_id: uuid.UUID) -> list[Change]:
    return db.query(Change).filter(Change.plan_id == plan_id).order_by(Change.created_at).all()
