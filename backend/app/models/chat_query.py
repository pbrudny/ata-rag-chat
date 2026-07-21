import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ChatQuery(Base):
    __tablename__ = "chat_queries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(5))
    answer_returned: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    top_similarity_score: Mapped[float | None] = mapped_column(Float)
    retrieved_chunk_ids: Mapped[list | None] = mapped_column(JSON)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("idx_chat_queries_answer_returned", "answer_returned"),)
