"""Plan retrieval and the approve/reject decision gate.

This is the one and only place a Plan is allowed to leave PENDING_APPROVAL —
the Code Generation Agent (added next) will refuse to act on anything that
hasn't passed through approve_plan() first.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from backend.models.enums import PlanStatus
from backend.models.plan import Plan
from backend.repositories import plan_repository
from backend.services.session_service import get_owned_session


def get_owned_plan(db: Session, plan_id: uuid.UUID, owner_id: uuid.UUID) -> Plan:
    plan = plan_repository.get_by_id(db, plan_id)
    if plan is None:
        raise NotFoundError("Plan not found")
    if plan.session.user_id != owner_id:
        raise ForbiddenError("You do not have access to this plan")
    return plan


def list_plans(db: Session, session_id: uuid.UUID, owner_id: uuid.UUID) -> list[Plan]:
    get_owned_session(db, session_id, owner_id)
    return plan_repository.list_by_session(db, session_id)


def approve_plan(db: Session, plan: Plan) -> Plan:
    if plan.status != PlanStatus.PENDING_APPROVAL:
        raise ConflictError(f"Plan is {plan.status.value}, not pending approval")
    plan.status = PlanStatus.APPROVED
    plan.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(plan)
    return plan


def reject_plan(db: Session, plan: Plan) -> Plan:
    if plan.status != PlanStatus.PENDING_APPROVAL:
        raise ConflictError(f"Plan is {plan.status.value}, not pending approval")
    plan.status = PlanStatus.REJECTED
    plan.rejected_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(plan)
    return plan
