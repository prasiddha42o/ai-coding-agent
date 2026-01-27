"""Plan model — the Planning Agent's proposed steps for a user request."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base
from backend.models.enums import ComplexityLevel, PlanStatus
from backend.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, enum_column

if TYPE_CHECKING:
    from backend.models.change import Change
    from backend.models.session import CodingSession


class Plan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "plans"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    user_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PlanStatus] = mapped_column(
        enum_column(PlanStatus, name="plan_status"), default=PlanStatus.PENDING_APPROVAL
    )
    complexity: Mapped[ComplexityLevel] = mapped_column(
        enum_column(ComplexityLevel, name="complexity_level"), default=ComplexityLevel.MODERATE
    )

    # Ordered list of {"title", "description", "affected_files"} produced by the
    # Planning Agent. Kept as JSON rather than a child table since steps are
    # only ever read/written as a unit, never queried individually.
    steps: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    affected_files: Mapped[list[str]] = mapped_column(JSONB, default=list)

    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped["CodingSession"] = relationship(back_populates="plans")
    changes: Mapped[list["Change"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )
