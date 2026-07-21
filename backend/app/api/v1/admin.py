from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_admin_auth
from app.db.session import get_db
from app.models.crawl_run import CrawlRun
from app.services import admin_service

router = APIRouter(dependencies=[Depends(require_admin_auth)])


@router.get("/summary")
def summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    result = admin_service.get_summary(db)
    return {
        "page_count": result.page_count,
        "chunk_count": result.chunk_count,
        "last_crawl": _serialize_crawl_run(result.last_crawl),
        "failed_page_count": result.failed_page_count,
        "avg_confidence": result.avg_confidence,
        "avg_latency_ms": result.avg_latency_ms,
    }


@router.get("/failed-pages")
def failed_pages(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    return [
        {"url": page.url, "http_status": page.http_status, "error_message": page.error_message}
        for page in admin_service.get_failed_pages(db)
    ]


@router.get("/questions")
def questions(db: Session = Depends(get_db)) -> dict[str, Any]:
    return {
        "top_questions": [
            {"question": question, "count": count}
            for question, count in admin_service.get_top_questions(db)
        ],
        "unanswered": [
            {"question": q.question, "created_at": q.created_at.isoformat()}
            for q in admin_service.get_unanswered_questions(db)
        ],
    }


def _serialize_crawl_run(run: CrawlRun | None) -> dict[str, Any] | None:
    if run is None:
        return None
    return {
        "id": str(run.id),
        "started_at": run.started_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "status": run.status,
        "pages_discovered": run.pages_discovered,
        "pages_updated": run.pages_updated,
        "pages_failed": run.pages_failed,
        "pages_removed": run.pages_removed,
    }
