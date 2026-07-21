"""Create crawl_runs table

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-21 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "crawl_runs",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("pages_discovered", sa.Integer, nullable=False, server_default="0"),
        sa.Column("pages_updated", sa.Integer, nullable=False, server_default="0"),
        sa.Column("pages_failed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("pages_removed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_summary", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("crawl_runs")
