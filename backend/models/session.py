"""CodingSession model — one natural-language task and everything it produced."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base
from backend.models.enums import SessionStatus
from backend.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, enum_column


class CodingSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sessions"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        enum_column(SessionStatus, name="session_status"), default=SessionStatus.ACTIVE
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    repository: Mapped["Repository"] = relationship(back_populates="sessions")
    plans: Mapped[list["Plan"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    test_runs: Mapped[list["TestRun"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    commits: Mapped[list["Commit"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
