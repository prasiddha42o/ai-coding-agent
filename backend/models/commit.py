"""Commit model — output of the Git & Session Agent for a coding session."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base
from backend.models.enums import CommitStatus
from backend.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, enum_column

if TYPE_CHECKING:
    from backend.models.session import CodingSession


class Commit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "commits"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    message: Mapped[str] = mapped_column(String(1024), nullable=False)
    diff_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    branch: Mapped[str] = mapped_column(String(255), default="main")
    sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[CommitStatus] = mapped_column(
        enum_column(CommitStatus, name="commit_status"), default=CommitStatus.DRAFT
    )

    session: Mapped["CodingSession"] = relationship(back_populates="commits")
