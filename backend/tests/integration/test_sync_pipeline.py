from unittest.mock import MagicMock

from sqlalchemy import select

import app.pipeline.sync as sync_module
from app.crawler.base import RawPage
from app.models.chunk import EMBEDDING_DIMENSIONS
from app.models.page import Page
from app.pipeline.sync import run_daily_sync

BASE_URL = "https://example.com/"
PAGE_A_URL = "https://example.com/a"


def _html_page(url: str, body_text: str) -> RawPage:
    html = f"<html><body><main><h1>{body_text}</h1><p>{body_text} content.</p></main></body></html>"
    return RawPage(url=url, status_code=200, content_type="html", body=html.encode("utf-8"))


class _FakeCrawler:
    """Deterministic stand-in for HttpxCrawler: `pages` maps url -> RawPage
    for whatever should be "discoverable" on a given sync run, and the
    dict can be mutated between calls to `run_daily_sync` to simulate a
    page disappearing from the live site."""

    def __init__(self, pages: dict[str, RawPage]):
        self.pages = pages

    def fetch(self, url: str) -> RawPage:
        return self.pages[url]

    def discover_links(self, page: RawPage) -> list[str]:
        # BFS visited-tracking in run_daily_sync handles dedup/cycles, so it's
        # fine to just point every page at every other known page.
        return [url for url in self.pages if url != page.url]


def _fake_embedding_client() -> MagicMock:
    client = MagicMock()

    def _create(model, input):
        response = MagicMock()
        response.data = [MagicMock(embedding=[0.001] * EMBEDDING_DIMENSIONS) for _ in input]
        return response

    client.embeddings.create.side_effect = _create
    return client


def test_new_pages_are_discovered_and_ingested(pg_db):
    crawler = _FakeCrawler(
        {
            BASE_URL: _html_page(BASE_URL, "Strona glowna"),
            PAGE_A_URL: _html_page(PAGE_A_URL, "Oferta"),
        }
    )

    run = run_daily_sync(
        pg_db, base_url=BASE_URL, crawler=crawler, embedding_client=_fake_embedding_client()
    )

    assert run.status == "success"
    assert run.pages_discovered == 2
    assert run.pages_updated == 2
    assert run.pages_failed == 0

    pages = pg_db.scalars(select(Page)).all()
    assert {p.url for p in pages} == {BASE_URL, PAGE_A_URL}
    assert all(p.consecutive_miss_count == 0 for p in pages)


def test_disappearing_page_is_only_deleted_after_threshold(pg_db):
    crawler = _FakeCrawler(
        {
            BASE_URL: _html_page(BASE_URL, "Strona glowna"),
            PAGE_A_URL: _html_page(PAGE_A_URL, "Oferta"),
        }
    )
    client = _fake_embedding_client()
    run_daily_sync(pg_db, base_url=BASE_URL, crawler=crawler, embedding_client=client)

    # Page A disappears from the site for the next 4 consecutive crawls.
    del crawler.pages[PAGE_A_URL]

    for expected_miss_count in (1, 2, 3):
        run_daily_sync(pg_db, base_url=BASE_URL, crawler=crawler, embedding_client=client)
        page_a = pg_db.scalar(select(Page).where(Page.url == PAGE_A_URL))
        assert page_a is not None, f"page should still exist after {expected_miss_count} miss(es)"
        assert page_a.consecutive_miss_count == expected_miss_count

    # 4th consecutive miss exceeds the threshold -> deleted.
    run = run_daily_sync(pg_db, base_url=BASE_URL, crawler=crawler, embedding_client=client)
    assert run.pages_removed == 1
    assert pg_db.scalar(select(Page).where(Page.url == PAGE_A_URL)) is None
    # The base page, still present on every crawl, is untouched.
    base_page = pg_db.scalar(select(Page).where(Page.url == BASE_URL))
    assert base_page is not None
    assert base_page.consecutive_miss_count == 0


def test_processing_failure_marks_page_failed_without_aborting_run(pg_db, monkeypatch):
    crawler = _FakeCrawler(
        {
            BASE_URL: _html_page(BASE_URL, "Strona glowna"),
            PAGE_A_URL: _html_page(PAGE_A_URL, "Oferta"),
        }
    )
    original_process = sync_module._process

    def _flaky_process(raw_page: RawPage):
        if raw_page.url == PAGE_A_URL:
            raise ValueError("boom: could not clean this page")
        return original_process(raw_page)

    monkeypatch.setattr(sync_module, "_process", _flaky_process)

    run = run_daily_sync(
        pg_db, base_url=BASE_URL, crawler=crawler, embedding_client=_fake_embedding_client()
    )

    assert run.status == "partial"
    assert run.pages_failed == 1
    assert run.pages_updated == 1

    failed_page = pg_db.scalar(select(Page).where(Page.url == PAGE_A_URL))
    assert failed_page is not None
    assert failed_page.status == "failed"
    assert "boom" in failed_page.error_message
