"""Tests for backend.services.repository_service: ZIP import (including its
zip-slip safety check), GitHub URL validation, ownership checks, and
deletion.
"""
import io
import zipfile

import pytest
from fastapi import UploadFile

from backend.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from backend.models.enums import RepositoryStatus
from backend.services import auth_service, repository_service


def _make_zip_upload(files: dict[str, str], filename: str = "project.zip") -> UploadFile:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path, content in files.items():
            archive.writestr(path, content)
    buffer.seek(0)
    return UploadFile(filename=filename, file=buffer)


def test_import_from_zip_creates_ready_repository(db_session, test_user):
    upload = _make_zip_upload(
        {
            "main.py": "def main():\n    pass\n",
            "requirements.txt": "fastapi\n",
        }
    )

    repository = repository_service.import_from_zip(db_session, test_user, upload, name="demo-project")

    assert repository.status == RepositoryStatus.READY
    assert repository.name == "demo-project"
    assert repository.metadata_json["language"] == "Python"
    assert repository.error_message is None

    repository_service.delete_repository(db_session, repository)


def test_import_from_zip_rejects_path_traversal(db_session, test_user):
    upload = _make_zip_upload({"../../etc/passwd": "malicious"})

    repository = repository_service.import_from_zip(db_session, test_user, upload, name="evil")

    # Import doesn't raise — it records the failure on the row so the caller
    # (an HTTP client) gets a 201 with status=error, not a 500.
    assert repository.status == RepositoryStatus.ERROR
    assert "Unsafe path" in repository.error_message

    repository_service.delete_repository(db_session, repository)


@pytest.mark.parametrize(
    "url",
    [
        "https://gitlab.com/owner/repo",
        "git@github.com:owner/repo.git",
        "file:///etc/passwd",
        "not a url",
    ],
)
def test_import_from_github_rejects_non_github_urls(db_session, test_user, url):
    with pytest.raises(ValidationAppError):
        repository_service.import_from_github(db_session, test_user, url, name=None, branch=None)


def test_get_owned_repository_rejects_other_users(db_session, test_user):
    upload = _make_zip_upload({"main.py": "print('hi')\n"})
    repository = repository_service.import_from_zip(db_session, test_user, upload, name="mine")

    other_user = auth_service.register_user(
        db_session, email="other.person@example.com", password="another-password", full_name=None
    )

    with pytest.raises(ForbiddenError):
        repository_service.get_owned_repository(db_session, repository.id, other_user.id)

    repository_service.delete_repository(db_session, repository)


def test_get_owned_repository_raises_not_found_for_unknown_id(db_session, test_user):
    import uuid

    with pytest.raises(NotFoundError):
        repository_service.get_owned_repository(db_session, uuid.uuid4(), test_user.id)


def test_delete_repository_removes_local_path(db_session, test_user):
    from pathlib import Path

    upload = _make_zip_upload({"main.py": "print('hi')\n"})
    repository = repository_service.import_from_zip(db_session, test_user, upload, name="to-delete")
    local_path = Path(repository.local_path)
    assert local_path.exists()

    repository_service.delete_repository(db_session, repository)

    assert not local_path.exists()
