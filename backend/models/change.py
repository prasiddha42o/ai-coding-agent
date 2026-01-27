"""Change model — a single file edit produced by the Code Generation Agent."""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base
from backend.models.enums import ChangeStatus, ChangeType
from backend.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, enum_column

if TYPE_CHECKING:
    from backend.models.plan import Plan


class Change(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "changes"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plans.id", ondelete="CASCADE"), index=True
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    change_type: Mapped[ChangeType] = mapped_column(enum_column(ChangeType, name="change_type"))
    status: Mapped[ChangeStatus] = mapped_column(
        enum_column(ChangeStatus, name="change_status"), default=ChangeStatus.PROPOSED
    )

    original_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    diff: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Findings from the Review Agent for this specific change, e.g.
    # [{"severity": "warning", "message": "unused import 'os'"}].
    review_notes: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    plan: Mapped["Plan"] = relationship(back_populates="changes")
