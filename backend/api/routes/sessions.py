"""Coding session endpoints — a session groups a repository, its prompt/plan
history, test runs, and commits into one auditable unit of work.
"""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.agents.planning_agent import create_plan
from backend.auth.dependencies import get_current_user
from backend.database.session import get_db
from backend.models.user import User
from backend.schemas.plan import PlanRead, PlanRequest
from backend.schemas.session import SessionRead
from backend.services import plan_service, session_service

router = APIRouter(tags=["sessions"])


@router.post(
    "/repositories/{repository_id}/sessions",
    response_model=SessionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return session_service.create_session(db, repository_id, current_user)


@router.get("/repositories/{repository_id}/sessions", response_model=list[SessionRead])
def list_sessions(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return session_service.list_sessions(db, repository_id, current_user.id)


@router.get("/sessions/{session_id}", response_model=SessionRead)
def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return session_service.get_owned_session(db, session_id, current_user.id)


@router.post(
    "/sessions/{session_id}/plans", response_model=PlanRead, status_code=status.HTTP_201_CREATED
)
def create_session_plan(
    session_id: uuid.UUID,
    payload: PlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = session_service.get_owned_session(db, session_id, current_user.id)
    return create_plan(db, session, payload.prompt)


@router.get("/sessions/{session_id}/plans", response_model=list[PlanRead])
def list_session_plans(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return plan_service.list_plans(db, session_id, current_user.id)
