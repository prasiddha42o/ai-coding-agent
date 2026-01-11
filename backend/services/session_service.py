"""CodingSession creation and ownership-checked retrieval."""
import uuid

from sqlalchemy.orm import Session

from backend.core.exceptions import ForbiddenError, NotFoundError
from backend.models.session import CodingSession
from backend.models.user import User
from backend.repositories import session_repository
from backend.services.repository_service import get_owned_repository


def create_session(db: Session, repository_id: uuid.UUID, owner: User) -> CodingSession:
    repository = get_owned_repository(db, repository_id, owner.id)
    session = session_repository.create(db, repository_id=repository.id, user_id=owner.id)
    db.commit()
    db.refresh(session)
    return session


def get_owned_session(db: Session, session_id: uuid.UUID, owner_id: uuid.UUID) -> CodingSession:
    session = session_repository.get_by_id(db, session_id)
    if session is None:
        raise NotFoundError("Session not found")
    if session.user_id != owner_id:
        raise ForbiddenError("You do not have access to this session")
    return session


def list_sessions(db: Session, repository_id: uuid.UUID, owner_id: uuid.UUID) -> list[CodingSession]:
    get_owned_repository(db, repository_id, owner_id)  # ownership check; raises if not owned
    return session_repository.list_by_repository(db, repository_id)
