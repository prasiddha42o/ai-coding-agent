"""File tree and file-content endpoints for the workspace UI."""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.core.exceptions import NotFoundError, ValidationAppError
from backend.database.session import get_db
from backend.models.user import User
from backend.schemas.file import FileContent, FileTreeNode
from backend.services import repository_service
from backend.tools.constants import LANGUAGE_EXTENSIONS
from backend.tools.file_tree import build_file_tree, is_binary_extension

router = APIRouter(prefix="/repositories/{repository_id}/files", tags=["files"])

_MAX_PREVIEW_BYTES = 2_000_000


@router.get("/tree", response_model=FileTreeNode)
def get_file_tree(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileTreeNode:
    repository = repository_service.get_owned_repository(db, repository_id, current_user.id)
    return build_file_tree(Path(repository.local_path))


@router.get("/content", response_model=FileContent)
def get_file_content(
    repository_id: uuid.UUID,
    path: str = Query(..., description="Repo-relative file path"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileContent:
    repository = repository_service.get_owned_repository(db, repository_id, current_user.id)
    repo_root = Path(repository.local_path).resolve()
    target = (repo_root / path).resolve()

    if not target.is_relative_to(repo_root):
        raise ValidationAppError("Invalid file path")
    if not target.is_file():
        raise NotFoundError("File not found")
    if is_binary_extension(target):
        raise ValidationAppError("Cannot preview a binary file")
    if target.stat().st_size > _MAX_PREVIEW_BYTES:
        raise ValidationAppError("File is too large to preview")

    content = target.read_text(encoding="utf-8", errors="replace")
    return FileContent(path=path, content=content, language=LANGUAGE_EXTENSIONS.get(target.suffix))
