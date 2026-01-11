"""add plan.summary

Revision ID: 57e4de4d69f5
Revises: 30b3482a3034
Create Date: 2026-01-08 19:26:03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "57e4de4d69f5"
down_revision: Union[str, None] = "30b3482a3034"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("summary", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("plans", "summary")
