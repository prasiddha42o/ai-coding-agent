"""Repository import, listing, refresh, and deletion endpoints."""
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.database.session import get_db
from backend.models.user import User
from backend.schemas.repository import RepositoryCreateFromGithub, RepositoryRead
from backend.services import repository_service

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.get("", response_model=list[RepositoryRead])
def list_repositories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    return repository_service.list_repositories(db, current_user.id)


@router.post("/github", response_model=RepositoryRead, status_code=status.HTTP_201_CREATED)
def import_github_repository(
    payload: RepositoryCreateFromGithub,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return repository_service.import_from_github(
        db, current_user, payload.source_url, payload.name, payload.branch
    )


@router.post("/zip", response_model=RepositoryRead, status_code=status.HTTP_201_CREATED)
def import_zip_repository(
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return repository_service.import_from_zip(db, current_user, file, name)


@router.get("/{repository_id}", response_model=RepositoryRead)
def get_repository(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return repository_service.get_owned_repository(db, repository_id, current_user.id)


@router.post("/{repository_id}/refresh", response_model=RepositoryRead)
def refresh_repository(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository = repository_service.get_owned_repository(db, repository_id, current_user.id)
    return repository_service.refresh_repository(db, repository)


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repository(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    repository = repository_service.get_owned_repository(db, repository_id, current_user.id)
    repository_service.delete_repository(db, repository)
