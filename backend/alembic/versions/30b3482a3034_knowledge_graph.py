"""knowledge graph tables

Revision ID: 30b3482a3034
Revises: 3edb28dd9467
Create Date: 2026-01-06 20:07:44
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "30b3482a3034"
down_revision: Union[str, None] = "3edb28dd9467"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_graph_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("language", sa.String(64), nullable=True),
        sa.Column("symbols", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_knowledge_graph_nodes_repository_id", "knowledge_graph_nodes", ["repository_id"]
    )
    op.create_unique_constraint(
        "uq_kg_node_repository_file_path",
        "knowledge_graph_nodes",
        ["repository_id", "file_path"],
    )

    op.create_table(
        "knowledge_graph_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_graph_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_graph_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("edge_type", sa.String(32), nullable=False, server_default="imports"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_knowledge_graph_edges_repository_id", "knowledge_graph_edges", ["repository_id"]
    )
    op.create_index("ix_knowledge_graph_edges_source_id", "knowledge_graph_edges", ["source_id"])
    op.create_index("ix_knowledge_graph_edges_target_id", "knowledge_graph_edges", ["target_id"])
    op.create_unique_constraint(
        "uq_kg_edge_source_target", "knowledge_graph_edges", ["source_id", "target_id"]
    )


def downgrade() -> None:
    op.drop_table("knowledge_graph_edges")
    op.drop_table("knowledge_graph_nodes")
