"""TestRun model — results from the Testing Agent executing a repo's test suite."""
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base
from backend.models.enums import TestRunner, TestStatus
from backend.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, enum_column


class TestRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "test_runs"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    runner: Mapped[TestRunner] = mapped_column(
        enum_column(TestRunner, name="test_runner"), default=TestRunner.UNKNOWN
    )
    command: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[TestStatus] = mapped_column(enum_column(TestStatus, name="test_status"))

    passed_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)

    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    stack_traces: Mapped[list[dict]] = mapped_column(JSONB, default=list)

    session: Mapped["CodingSession"] = relationship(back_populates="test_runs")
