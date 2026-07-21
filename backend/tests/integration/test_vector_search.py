from datetime import UTC, datetime

from app.models.chunk import EMBEDDING_DIMENSIONS, Chunk
from app.models.page import Page
from app.retrieval.vector_search import search_chunks


def _vector(active_index: int) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    vector[active_index] = 1.0
    return vector


def _make_page_and_chunk(db, url: str, content: str, embedding: list[float]) -> Chunk:
    page = Page(
        url=url,
        title="Test Page",
        source_type="html",
        language="en",
        content_hash=f"hash-{url}",
        last_crawled_at=datetime.now(UTC),
    )
    db.add(page)
    db.flush()
    chunk = Chunk(
        page_id=page.id,
        document_id=str(page.id),
        chunk_index=0,
        content=content,
        content_hash=f"chash-{url}",
        section="Test",
        token_count=10,
        language="en",
        url=url,
        title="Test Page",
        source_type="html",
        embedding=embedding,
        embedding_model="text-embedding-3-small",
    )
    db.add(chunk)
    db.flush()
    return chunk


def test_search_returns_closest_chunk_first(pg_db):
    close_chunk = _make_page_and_chunk(
        pg_db, "https://example.com/a", "About tuition fees", _vector(0)
    )
    far_chunk = _make_page_and_chunk(
        pg_db, "https://example.com/b", "About campus map", _vector(500)
    )

    results = search_chunks(pg_db, _vector(0), top_k=2)

    assert results[0].chunk.id == close_chunk.id
    assert results[0].similarity > results[1].similarity
    assert results[1].chunk.id == far_chunk.id


def test_search_respects_top_k(pg_db):
    for i in range(5):
        _make_page_and_chunk(pg_db, f"https://example.com/page{i}", f"content {i}", _vector(i))

    results = search_chunks(pg_db, _vector(0), top_k=3)

    assert len(results) == 3


def test_search_similarity_is_one_for_identical_vector(pg_db):
    _make_page_and_chunk(pg_db, "https://example.com/exact", "Exact match", _vector(42))

    results = search_chunks(pg_db, _vector(42), top_k=1)

    assert results[0].similarity == 1.0
