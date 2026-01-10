"""Repository model — an imported codebase owned by a user."""
import uuid
from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base
from backend.models.enums import RepositorySourceType, RepositoryStatus
from backend.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Repository(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "repositories"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[RepositorySourceType] = mapped_column(
        SAEnum(RepositorySourceType, name="repository_source_type")
    )
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    default_branch: Mapped[str] = mapped_column(String(255), default="main")
    local_path: Mapped[str] = mapped_column(String(1024), nullable=False)

    status: Mapped[RepositoryStatus] = mapped_column(
        SAEnum(RepositoryStatus, name="repository_status"), default=RepositoryStatus.PENDING
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Auto-extracted metadata: primary language, framework, build tool, package
    # manager, dependency/config file paths — see tools/metadata_extractor.py.
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="repositories")
    files: Mapped[list["File"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["CodingSession"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
    knowledge_graph_nodes: Mapped[list["KnowledgeGraphNode"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
