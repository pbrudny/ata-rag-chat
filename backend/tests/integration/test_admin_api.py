from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core import security
from app.db.session import get_db
from app.main import app
from app.models.chat_query import ChatQuery
from app.models.crawl_run import CrawlRun
from app.models.page import Page


def _client(pg_db) -> TestClient:
    def _override_db():
        yield pg_db

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app)


def _set_admin_credentials(monkeypatch) -> tuple[str, str]:
    monkeypatch.setattr(security.settings, "basic_auth_user", "admin")
    monkeypatch.setattr(security.settings, "basic_auth_password", "secret")
    return "admin", "secret"


def test_admin_endpoints_require_auth(pg_db, monkeypatch):
    _set_admin_credentials(monkeypatch)

    with _client(pg_db) as client:
        response = client.get("/api/admin/summary")
    app.dependency_overrides.clear()

    assert response.status_code == 401


def test_admin_endpoints_reject_wrong_credentials(pg_db, monkeypatch):
    _set_admin_credentials(monkeypatch)

    with _client(pg_db) as client:
        response = client.get("/api/admin/summary", auth=("admin", "wrong-password"))
    app.dependency_overrides.clear()

    assert response.status_code == 401


def test_admin_summary_reports_aggregates(pg_db, monkeypatch):
    credentials = _set_admin_credentials(monkeypatch)

    pg_db.add_all(
        [
            Page(
                url="https://akademiata.pl/a",
                title="A",
                source_type="html",
                language="pl",
                content_hash="h1",
                last_crawled_at=datetime.now(UTC),
                status="active",
            ),
            Page(
                url="https://akademiata.pl/broken",
                source_type="html",
                content_hash="",
                last_crawled_at=datetime.now(UTC),
                status="failed",
                error_message="boom",
            ),
        ]
    )
    pg_db.add(
        CrawlRun(
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
            status="success",
            pages_discovered=2,
            pages_updated=1,
            pages_failed=1,
            pages_removed=0,
        )
    )
    pg_db.add(
        ChatQuery(
            question="Kiedy jest rekrutacja?",
            language="pl",
            answer_returned=True,
            confidence_score=0.8,
            top_similarity_score=0.85,
            latency_ms=500,
        )
    )
    pg_db.commit()

    with _client(pg_db) as client:
        response = client.get("/api/admin/summary", auth=credentials)
    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["page_count"] == 2
    assert body["failed_page_count"] == 1
    assert body["last_crawl"]["status"] == "success"
    assert body["avg_confidence"] == 0.8


def test_admin_failed_pages_lists_only_failed(pg_db, monkeypatch):
    credentials = _set_admin_credentials(monkeypatch)

    pg_db.add_all(
        [
            Page(
                url="https://akademiata.pl/ok",
                source_type="html",
                content_hash="h",
                last_crawled_at=datetime.now(UTC),
                status="active",
            ),
            Page(
                url="https://akademiata.pl/broken",
                source_type="html",
                content_hash="",
                last_crawled_at=datetime.now(UTC),
                status="failed",
                error_message="timeout",
                http_status=504,
            ),
        ]
    )
    pg_db.commit()

    with _client(pg_db) as client:
        response = client.get("/api/admin/failed-pages", auth=credentials)
    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["url"] == "https://akademiata.pl/broken"
    assert body[0]["error_message"] == "timeout"


def test_admin_questions_reports_top_and_unanswered(pg_db, monkeypatch):
    credentials = _set_admin_credentials(monkeypatch)

    pg_db.add_all(
        [
            ChatQuery(question="Ile kosztuje czesne?", answer_returned=True, confidence_score=0.9),
            ChatQuery(question="Ile kosztuje czesne?", answer_returned=True, confidence_score=0.9),
            ChatQuery(question="Jaka jest pogoda?", answer_returned=False, confidence_score=0.1),
        ]
    )
    pg_db.commit()

    with _client(pg_db) as client:
        response = client.get("/api/admin/questions", auth=credentials)
    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["top_questions"][0] == {"question": "Ile kosztuje czesne?", "count": 2}
    assert len(body["unanswered"]) == 1
    assert body["unanswered"][0]["question"] == "Jaka jest pogoda?"
