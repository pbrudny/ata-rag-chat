"""Create chat_queries table

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-21 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chat_queries",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()
        ),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("language", sa.String(5), nullable=True),
        sa.Column("answer_returned", sa.Boolean, nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("top_similarity_score", sa.Float, nullable=True),
        sa.Column("retrieved_chunk_ids", sa.JSON, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("idx_chat_queries_answer_returned", "chat_queries", ["answer_returned"])


def downgrade() -> None:
    op.drop_index("idx_chat_queries_answer_returned", table_name="chat_queries")
    op.drop_table("chat_queries")
