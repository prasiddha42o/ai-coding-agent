"""Plan retrieval, the approve/reject decision gate, and code generation."""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.agents.code_generation_agent import generate_changes
from backend.auth.dependencies import get_current_user
from backend.database.session import get_db
from backend.models.user import User
from backend.repositories import change_repository
from backend.schemas.change import ChangeRead
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


@router.post(
    "/{plan_id}/generate", response_model=list[ChangeRead], status_code=status.HTTP_201_CREATED
)
def generate_plan_changes(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = plan_service.get_owned_plan(db, plan_id, current_user.id)
    return generate_changes(db, plan)


@router.get("/{plan_id}/changes", response_model=list[ChangeRead])
def list_plan_changes(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan_service.get_owned_plan(db, plan_id, current_user.id)
    return change_repository.list_by_plan(db, plan_id)
