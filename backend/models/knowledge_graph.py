"""Knowledge graph models — one node per source file, edges for resolved imports.

Deliberately file-grained rather than one row per function/class: it keeps
the graph small enough to load and traverse in memory per-repository while
still matching the PRD's component-relationship view (e.g. "Auth Service ->
User Model -> JWT Middleware"). Per-file symbols (functions/classes) from
tree-sitter are attached as JSON on the node instead of becoming their own
rows.
"""
import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.session import Base
from backend.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeGraphNode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_graph_nodes"
    __table_args__ = (
        UniqueConstraint("repository_id", "file_path", name="uq_kg_node_repository_file_path"),
    )

    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), index=True
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    symbols: Mapped[list[dict]] = mapped_column(JSONB, default=list)

    repository: Mapped["Repository"] = relationship(back_populates="knowledge_graph_nodes")


class KnowledgeGraphEdge(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_graph_edges"
    __table_args__ = (
        UniqueConstraint("source_id", "target_id", name="uq_kg_edge_source_target"),
    )

    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), index=True
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_graph_nodes.id", ondelete="CASCADE"), index=True
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_graph_nodes.id", ondelete="CASCADE"), index=True
    )
    edge_type: Mapped[str] = mapped_column(String(32), default="imports")
