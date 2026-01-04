"""Pydantic schemas for Plan."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.models.enums import ComplexityLevel, PlanStatus


class PlanRequest(BaseModel):
    """A natural-language task submitted against a repository session."""

    prompt: str


class PlanStep(BaseModel):
    title: str
    description: str
    affected_files: list[str] = []


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    user_prompt: str
    status: PlanStatus
    complexity: ComplexityLevel
    steps: list[PlanStep]
    affected_files: list[str]
    approved_at: datetime | None
    rejected_at: datetime | None
    created_at: datetime
