"""Repository import (GitHub clone / ZIP upload), refresh, and deletion."""
import logging
import re
import shutil
import uuid
from pathlib import Path

import git
from fastapi import UploadFile
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from backend.models.enums import RepositorySourceType, RepositoryStatus
from backend.models.repository import Repository
from backend.models.user import User
from backend.repositories import repository_repository
from backend.utils.fs import flatten_single_root, safe_extract_zip, slugify

logger = logging.getLogger(__name__)

# Restricted to https://github.com/<owner>/<repo> to avoid the clone target
# being used as an SSRF/arbitrary-command vector (no ssh://, file://, or
# other-host URLs).
_GITHUB_URL_RE = re.compile(r"^https://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$")


def _validate_github_url(url: str) -> re.Match:
    match = _GITHUB_URL_RE.match(url.strip())
    if not match:
        raise ValidationAppError(
            "source_url must look like https://github.com/<owner>/<repo>"
        )
    return match


def get_owned_repository(db: Session, repository_id: uuid.UUID, owner_id: uuid.UUID) -> Repository:
    repository = repository_repository.get_by_id(db, repository_id)
    if repository is None:
        raise NotFoundError("Repository not found")
    if repository.owner_id != owner_id:
        raise ForbiddenError("You do not have access to this repository")
    return repository


def list_repositories(db: Session, owner_id: uuid.UUID) -> list[Repository]:
    return repository_repository.list_by_owner(db, owner_id)


def import_from_github(
    db: Session, owner: User, source_url: str, name: str | None, branch: str | None
) -> Repository:
    match = _validate_github_url(source_url)
    settings = get_settings()
    repository_id = uuid.uuid4()
    local_path = Path(settings.workspaces_dir) / str(repository_id)

    repository = repository_repository.create(
        db,
        id=repository_id,
        owner_id=owner.id,
        name=name or slugify(match.group(2)),
        source_type=RepositorySourceType.GITHUB,
        source_url=source_url,
        default_branch=branch or "main",
        local_path=str(local_path),
        status=RepositoryStatus.CLONING,
    )
    db.commit()

    try:
        clone_kwargs = {"depth": 1}
        if branch:
            clone_kwargs["branch"] = branch
        git.Repo.clone_from(source_url, str(local_path), **clone_kwargs)
    except Exception as exc:  # noqa: BLE001 — surfaced as repository.error_message, not a 500
        logger.exception("GitHub clone failed for %s", source_url)
        repository.status = RepositoryStatus.ERROR
        repository.error_message = f"Clone failed: {exc}"
        db.commit()
        return repository

    repository.status = RepositoryStatus.PENDING  # awaiting the metadata/indexing pass
    db.commit()
    return repository


def import_from_zip(db: Session, owner: User, upload_file: UploadFile, name: str | None) -> Repository:
    settings = get_settings()
    repository_id = uuid.uuid4()
    local_path = Path(settings.workspaces_dir) / str(repository_id)
    max_bytes = settings.max_upload_size_mb * 1024 * 1024

    repository = repository_repository.create(
        db,
        id=repository_id,
        owner_id=owner.id,
        name=name or slugify(upload_file.filename or "repository"),
        source_type=RepositorySourceType.ZIP,
        source_url=None,
        default_branch="main",
        local_path=str(local_path),
        status=RepositoryStatus.CLONING,
    )
    db.commit()

    tmp_zip_path = Path(settings.uploads_dir) / f"{repository_id}.zip"
    tmp_zip_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        size_written = 0
        with open(tmp_zip_path, "wb") as out:
            while chunk := upload_file.file.read(1024 * 1024):
                size_written += len(chunk)
                if size_written > max_bytes:
                    raise ValidationAppError(
                        f"Upload exceeds the {settings.max_upload_size_mb}MB limit"
                    )
                out.write(chunk)

        safe_extract_zip(tmp_zip_path, local_path, max_bytes)
        flatten_single_root(local_path)
    except Exception as exc:  # noqa: BLE001
        logger.exception("ZIP import failed for repository %s", repository_id)
        shutil.rmtree(local_path, ignore_errors=True)
        repository.status = RepositoryStatus.ERROR
        repository.error_message = str(exc)
        db.commit()
        return repository
    finally:
        tmp_zip_path.unlink(missing_ok=True)

    repository.status = RepositoryStatus.PENDING
    db.commit()
    return repository


def refresh_repository(db: Session, repository: Repository) -> Repository:
    if repository.source_type != RepositorySourceType.GITHUB:
        raise ValidationAppError("Only GitHub-sourced repositories can be refreshed")

    try:
        repo = git.Repo(repository.local_path)
        repo.remotes.origin.pull()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Refresh failed for repository %s", repository.id)
        repository.status = RepositoryStatus.ERROR
        repository.error_message = f"Refresh failed: {exc}"
        db.commit()
        return repository

    repository.status = RepositoryStatus.PENDING
    repository.error_message = None
    db.commit()
    return repository


def delete_repository(db: Session, repository: Repository) -> None:
    shutil.rmtree(repository.local_path, ignore_errors=True)
    repository_repository.delete(db, repository)
    db.commit()
