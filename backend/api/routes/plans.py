"""Plan retrieval and the approve/reject decision gate."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.database.session import get_db
from backend.models.user import User
from backend.schemas.plan import PlanRead
from backend.services import plan_service

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("/{plan_id}", response_model=PlanRead)
def get_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return plan_service.get_owned_plan(db, plan_id, current_user.id)


@router.post("/{plan_id}/approve", response_model=PlanRead)
def approve_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = plan_service.get_owned_plan(db, plan_id, current_user.id)
    return plan_service.approve_plan(db, plan)


@router.post("/{plan_id}/reject", response_model=PlanRead)
def reject_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = plan_service.get_owned_plan(db, plan_id, current_user.id)
    return plan_service.reject_plan(db, plan)
