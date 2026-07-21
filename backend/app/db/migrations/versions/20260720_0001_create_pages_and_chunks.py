"""Create pages and chunks tables

Revision ID: 0001
Revises:
Create Date: 2026-07-20 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIMENSIONS = 1536  # text-embedding-3-small


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "pages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("url", sa.Text, nullable=False, unique=True),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("source_type", sa.String(10), nullable=False),
        sa.Column("language", sa.String(5), nullable=True),
        sa.Column("content_hash", sa.Text, nullable=False),
        sa.Column("last_modified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="active"),
        sa.Column("http_status", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("consecutive_miss_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_pages_status", "pages", ["status"])
    op.create_index("idx_pages_content_hash", "pages", ["content_hash"])

    op.create_table(
        "chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column(
            "page_id",
            UUID(as_uuid=True),
            sa.ForeignKey("pages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("document_id", sa.Text, nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("content_hash", sa.Text, nullable=False),
        sa.Column("section", sa.Text, nullable=True),
        sa.Column("token_count", sa.Integer, nullable=False),
        sa.Column("language", sa.String(5), nullable=True),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("source_type", sa.String(10), nullable=False),
        sa.Column("last_modified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=False),
        sa.Column("embedding_model", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_chunks_page_id", "chunks", ["page_id"])
    op.create_index("idx_chunks_content_hash", "chunks", ["page_id", "content_hash"])


def downgrade() -> None:
    op.drop_index("idx_chunks_content_hash", table_name="chunks")
    op.drop_index("idx_chunks_page_id", table_name="chunks")
    op.drop_table("chunks")
    op.drop_index("idx_pages_content_hash", table_name="pages")
    op.drop_index("idx_pages_status", table_name="pages")
    op.drop_table("pages")
