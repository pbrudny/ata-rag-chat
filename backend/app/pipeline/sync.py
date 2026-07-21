import hashlib
import logging
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crawler.base import RawPage
from app.crawler.httpx_crawler import HttpxCrawler
from app.models.crawl_run import CrawlRun
from app.models.page import Page
from app.pipeline.crawl_page import ProcessedPage, process_html_page, process_pdf_page
from app.pipeline.ingest import ingest_page

logger = logging.getLogger(__name__)

MAX_CONSECUTIVE_MISSES = 3
PDF_STORAGE_DIR = Path(__file__).resolve().parents[2] / "data" / "crawled_pdfs"


def run_daily_sync(
    db: Session,
    base_url: str | None = None,
    crawler: HttpxCrawler | None = None,
    *,
    embedding_client: OpenAI | None = None,
) -> CrawlRun:
    """Crawl the whole site, incrementally ingest every page, then clean up
    pages that have been missing from `MAX_CONSECUTIVE_MISSES` consecutive
    daily crawls."""
    base_url = base_url or settings.crawl_base_url
    crawler = crawler or HttpxCrawler(base_url)

    run = CrawlRun(started_at=datetime.now(UTC), status="running")
    db.add(run)
    db.commit()

    discovered_urls: set[str] = set()
    pages_updated = 0
    pages_failed = 0

    try:
        for raw_page in _crawl_site(crawler, base_url):
            discovered_urls.add(raw_page.url)
            try:
                processed = _process(raw_page)
                ingest_page(db, processed, embedding_client=embedding_client)
                pages_updated += 1
            except Exception as exc:  # noqa: BLE001 - one bad page must not abort the run
                logger.exception("Failed to process page %s", raw_page.url)
                _record_failed_page(db, raw_page, exc)
                pages_failed += 1

        pages_removed = _cleanup_stale_pages(db, discovered_urls)

        run.status = "success" if pages_failed == 0 else "partial"
        run.pages_discovered = len(discovered_urls)
        run.pages_updated = pages_updated
        run.pages_failed = pages_failed
        run.pages_removed = pages_removed
    except Exception as exc:  # noqa: BLE001 - record the failure, don't propagate
        logger.exception("Daily sync run failed")
        run.status = "failed"
        run.error_summary = str(exc)[:2000]
        # TODO: notify via Discord bot once an alert channel ID is configured (deferred).
    finally:
        run.finished_at = datetime.now(UTC)
        db.commit()

    return run


def _crawl_site(crawler: HttpxCrawler, base_url: str) -> Iterator[RawPage]:
    visited: set[str] = set()
    queue: list[str] = [base_url]

    while queue:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            page = crawler.fetch(url)
        except Exception:
            logger.exception("Failed to fetch %s", url)
            continue

        yield page

        if page.content_type == "html":
            for link in crawler.discover_links(page):
                if link not in visited:
                    queue.append(link)


def _process(raw_page: RawPage) -> ProcessedPage:
    if raw_page.content_type == "pdf":
        pdf_path = _save_pdf(raw_page)
        return process_pdf_page(raw_page, pdf_path)
    return process_html_page(raw_page)


def _save_pdf(raw_page: RawPage) -> Path:
    PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(raw_page.body).hexdigest()
    path = PDF_STORAGE_DIR / f"{digest}.pdf"
    path.write_bytes(raw_page.body)
    return path


def _record_failed_page(db: Session, raw_page: RawPage, error: Exception) -> None:
    page = db.scalar(select(Page).where(Page.url == raw_page.url))
    now = datetime.now(UTC)
    source_type = raw_page.content_type if raw_page.content_type in ("html", "pdf") else "html"

    if page is None:
        db.add(
            Page(
                url=raw_page.url,
                source_type=source_type,
                content_hash="",
                last_crawled_at=now,
                status="failed",
                http_status=raw_page.status_code,
                error_message=str(error)[:2000],
            )
        )
    else:
        page.status = "failed"
        page.http_status = raw_page.status_code
        page.error_message = str(error)[:2000]
        page.last_crawled_at = now
    db.commit()


def _cleanup_stale_pages(db: Session, discovered_urls: set[str]) -> int:
    """Pages missing from `MAX_CONSECUTIVE_MISSES` consecutive crawls are
    deleted; a single transient miss just increments the counter."""
    pages = db.scalars(select(Page).where(Page.status.in_(["active", "failed"]))).all()
    removed = 0

    for page in pages:
        if page.url in discovered_urls:
            page.consecutive_miss_count = 0
            continue
        page.consecutive_miss_count += 1
        if page.consecutive_miss_count > MAX_CONSECUTIVE_MISSES:
            db.delete(page)
            removed += 1

    db.commit()
    return removed
