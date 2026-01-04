"""Pydantic schemas for CodingSession."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.models.enums import SessionStatus


class SessionCreate(BaseModel):
    repository_id: uuid.UUID


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repository_id: uuid.UUID
    user_id: uuid.UUID
    title: str | None
    status: SessionStatus
    created_at: datetime
    completed_at: datetime | None
