"""Pydantic schemas for Commit."""
import uuid

from pydantic import BaseModel, ConfigDict

from backend.models.enums import CommitStatus


class CommitCreateRequest(BaseModel):
    message_override: str | None = None


class CommitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    message: str
    diff_summary: str | None
    branch: str
    sha: str | None
    status: CommitStatus
