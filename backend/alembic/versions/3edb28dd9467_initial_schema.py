"""initial schema

Revision ID: 3edb28dd9467
Revises:
Create Date: 2026-01-04 19:42:11
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "3edb28dd9467"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)

    op.create_table(
        "repositories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum("github", "zip", name="repository_source_type"),
            nullable=False,
        ),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("default_branch", sa.String(255), nullable=False, server_default="main"),
        sa.Column("local_path", sa.String(1024), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "cloning", "indexing", "ready", "error", name="repository_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("last_indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_repositories_owner_id", "repositories", ["owner_id"])

    op.create_table(
        "files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("path", sa.String(1024), nullable=False),
        sa.Column("language", sa.String(64), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("is_binary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_files_repository_id", "files", ["repository_id"])
    op.create_index("ix_files_path", "files", ["path"])

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "completed", "failed", name="session_status"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sessions_repository_id", "sessions", ["repository_id"])
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])

    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_prompt", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending_approval",
                "approved",
                "rejected",
                "executing",
                "completed",
                "failed",
                name="plan_status",
            ),
            nullable=False,
            server_default="pending_approval",
        ),
        sa.Column(
            "complexity",
            sa.Enum("trivial", "moderate", "complex", name="complexity_level"),
            nullable=False,
            server_default="moderate",
        ),
        sa.Column("steps", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("affected_files", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_plans_session_id", "plans", ["session_id"])

    op.create_table(
        "changes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column(
            "change_type", sa.Enum("create", "modify", "delete", name="change_type"), nullable=False
        ),
        sa.Column(
            "status",
            sa.Enum("proposed", "applied", "reverted", name="change_status"),
            nullable=False,
            server_default="proposed",
        ),
        sa.Column("original_content", sa.Text(), nullable=True),
        sa.Column("new_content", sa.Text(), nullable=True),
        sa.Column("diff", sa.Text(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("review_notes", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_changes_plan_id", "changes", ["plan_id"])

    op.create_table(
        "test_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "runner",
            sa.Enum("pytest", "jest", "npm", "unknown", name="test_runner"),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column("command", sa.String(1024), nullable=False),
        sa.Column(
            "status", sa.Enum("passed", "failed", "error", "skipped", name="test_status"), nullable=False
        ),
        sa.Column("passed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output", sa.Text(), nullable=True),
        sa.Column("stack_traces", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_test_runs_session_id", "test_runs", ["session_id"])

    op.create_table(
        "commits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("message", sa.String(1024), nullable=False),
        sa.Column("diff_summary", sa.Text(), nullable=True),
        sa.Column("branch", sa.String(255), nullable=False, server_default="main"),
        sa.Column("sha", sa.String(64), nullable=True),
        sa.Column(
            "status",
            sa.Enum("draft", "committed", name="commit_status"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_commits_session_id", "commits", ["session_id"])


def downgrade() -> None:
    op.drop_table("commits")
    sa.Enum(name="commit_status").drop(op.get_bind(), checkfirst=True)

    op.drop_table("test_runs")
    sa.Enum(name="test_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="test_runner").drop(op.get_bind(), checkfirst=True)

    op.drop_table("changes")
    sa.Enum(name="change_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="change_type").drop(op.get_bind(), checkfirst=True)

    op.drop_table("plans")
    sa.Enum(name="complexity_level").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="plan_status").drop(op.get_bind(), checkfirst=True)

    op.drop_table("sessions")
    sa.Enum(name="session_status").drop(op.get_bind(), checkfirst=True)

    op.drop_table("files")

    op.drop_table("repositories")
    sa.Enum(name="repository_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="repository_source_type").drop(op.get_bind(), checkfirst=True)

    op.drop_table("refresh_tokens")

    op.drop_table("users")
