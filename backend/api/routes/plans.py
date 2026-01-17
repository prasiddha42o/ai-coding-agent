"""Plan retrieval, the approve/reject decision gate, and code generation."""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.agents.code_generation_agent import generate_changes
from backend.agents.git_session_agent import create_commit
from backend.agents.review_agent import review_changes
from backend.auth.dependencies import get_current_user
from backend.database.session import get_db
from backend.models.user import User
from backend.repositories import change_repository
from backend.schemas.change import ChangeRead
from backend.schemas.commit import CommitRead
from backend.schemas.plan import PlanRead
from backend.schemas.review import ReviewResponse
from backend.services import change_service, plan_service

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


@router.post("/{plan_id}/review", response_model=ReviewResponse)
def review_plan_changes(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = plan_service.get_owned_plan(db, plan_id, current_user.id)
    summary = review_changes(db, plan)
    changes = change_repository.list_by_plan(db, plan_id)
    return ReviewResponse(summary=summary, changes=changes)


@router.post("/{plan_id}/apply", response_model=list[ChangeRead])
def apply_plan_changes(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = plan_service.get_owned_plan(db, plan_id, current_user.id)
    return change_service.apply_changes(db, plan)


@router.post("/{plan_id}/commit", response_model=CommitRead, status_code=status.HTTP_201_CREATED)
def commit_plan_changes(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = plan_service.get_owned_plan(db, plan_id, current_user.id)
    return create_commit(db, plan)
