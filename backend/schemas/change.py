"""Pydantic schemas for Change."""
import uuid

from pydantic import BaseModel, ConfigDict

from backend.models.enums import ChangeStatus, ChangeType


class ReviewNote(BaseModel):
    severity: str
    message: str
    line: int | None = None


class ChangeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan_id: uuid.UUID
    file_path: str
    change_type: ChangeType
    status: ChangeStatus
    diff: str | None
    explanation: str | None
    review_notes: list[ReviewNote] | None
