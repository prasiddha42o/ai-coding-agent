"""Pydantic schemas for TestRun."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.models.enums import TestRunner, TestStatus


class StackTrace(BaseModel):
    test_name: str
    message: str
    trace: str | None = None


class TestRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    runner: TestRunner
    command: str
    status: TestStatus
    passed_count: int
    failed_count: int
    skipped_count: int
    duration_ms: int
    output: str | None
    stack_traces: list[StackTrace]
    created_at: datetime
