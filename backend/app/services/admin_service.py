from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.chat_query import ChatQuery
from app.models.chunk import Chunk
from app.models.crawl_run import CrawlRun
from app.models.page import Page


@dataclass(frozen=True)
class AdminSummary:
    page_count: int
    chunk_count: int
    last_crawl: CrawlRun | None
    failed_page_count: int
    avg_confidence: float | None
    avg_latency_ms: float | None


def get_summary(db: Session) -> AdminSummary:
    return AdminSummary(
        page_count=db.scalar(select(func.count()).select_from(Page)) or 0,
        chunk_count=db.scalar(select(func.count()).select_from(Chunk)) or 0,
        last_crawl=db.scalar(select(CrawlRun).order_by(CrawlRun.started_at.desc()).limit(1)),
        failed_page_count=db.scalar(
            select(func.count()).select_from(Page).where(Page.status == "failed")
        )
        or 0,
        avg_confidence=db.scalar(select(func.avg(ChatQuery.confidence_score))),
        avg_latency_ms=db.scalar(select(func.avg(ChatQuery.latency_ms))),
    )


def get_failed_pages(db: Session, limit: int = 50) -> list[Page]:
    query = (
        select(Page).where(Page.status == "failed").order_by(Page.updated_at.desc()).limit(limit)
    )
    return list(db.scalars(query).all())


def get_top_questions(db: Session, limit: int = 10) -> list[tuple[str, int]]:
    query = (
        select(ChatQuery.question, func.count().label("count"))
        .group_by(ChatQuery.question)
        .order_by(func.count().desc())
        .limit(limit)
    )
    return [(row.question, row.count) for row in db.execute(query).all()]


def get_unanswered_questions(db: Session, limit: int = 50) -> list[ChatQuery]:
    query = (
        select(ChatQuery)
        .where(ChatQuery.answer_returned.is_(False))
        .order_by(ChatQuery.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(query).all())
