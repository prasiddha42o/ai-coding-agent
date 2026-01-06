"""Data-access layer for Repository — thin query wrappers, no business logic."""
import uuid

from sqlalchemy.orm import Session

from backend.models.repository import Repository


def get_by_id(db: Session, repository_id: uuid.UUID) -> Repository | None:
    return db.get(Repository, repository_id)


def list_by_owner(db: Session, owner_id: uuid.UUID) -> list[Repository]:
    return (
        db.query(Repository)
        .filter(Repository.owner_id == owner_id)
        .order_by(Repository.created_at.desc())
        .all()
    )


def create(db: Session, **fields) -> Repository:
    repository = Repository(**fields)
    db.add(repository)
    db.flush()
    return repository


def delete(db: Session, repository: Repository) -> None:
    db.delete(repository)
    db.flush()
