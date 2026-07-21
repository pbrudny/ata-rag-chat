import hashlib
from unittest.mock import MagicMock

from sqlalchemy import select

from app.chunking.chunker import count_tokens
from app.models.chunk import Chunk
from app.pipeline.crawl_page import ProcessedPage
from app.pipeline.ingest import ingest_page

URL = "https://akademiata.pl/oferta"

_SENTENCE_A = "Informatyka jest jednym z najpopularniejszych kierunkow na AkademiaTA. "
_SENTENCE_A_EDITED = (
    "Informatyka i sztuczna inteligencja to najpopularniejsze kierunki na AkademiaTA. "
)
_SENTENCE_B = "Kontakt z dziekanatem jest mozliwy od poniedziałku do piatku. "


def _n_token_text(sentence: str, n_tokens: int) -> str:
    text = ""
    while count_tokens(text) < n_tokens:
        text += sentence
    return text.strip()


def _markdown(section_a_sentence: str) -> str:
    section_a = f"# Sekcja A\n\n{_n_token_text(section_a_sentence, 780)}"
    section_b = f"# Sekcja B\n\n{_n_token_text(_SENTENCE_B, 780)}"
    return f"{section_a}\n\n{section_b}\n"


def _processed_page(markdown: str) -> ProcessedPage:
    return ProcessedPage(
        url=URL,
        title="Oferta",
        markdown=markdown,
        language="pl",
        source_type="html",
        content_hash=hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        http_status=200,
    )


def _fake_openai_client():
    client = MagicMock()
    calls: list[list[str]] = []

    def _create(model, input):
        calls.append(list(input))
        response = MagicMock()
        response.data = [MagicMock(embedding=[0.001] * 1536) for _ in input]
        return response

    client.embeddings.create.side_effect = _create
    return client, calls


def test_new_page_embeds_all_chunks(pg_db):
    client, calls = _fake_openai_client()
    markdown = _markdown(_SENTENCE_A)

    result = ingest_page(pg_db, _processed_page(markdown), embedding_client=client)

    assert result.skipped is False
    assert result.chunks_created == 2
    assert result.chunks_reused == 0
    assert result.chunks_deleted == 0
    assert len(calls) == 1
    assert len(calls[0]) == 2

    chunk_count = len(pg_db.scalars(select(Chunk).where(Chunk.page_id == result.page_id)).all())
    assert chunk_count == 2


def test_unchanged_page_triggers_zero_embedding_calls(pg_db):
    client, calls = _fake_openai_client()
    markdown = _markdown(_SENTENCE_A)

    ingest_page(pg_db, _processed_page(markdown), embedding_client=client)
    calls.clear()

    result = ingest_page(pg_db, _processed_page(markdown), embedding_client=client)

    assert result.skipped is True
    assert calls == []


def test_changed_section_only_reembeds_that_chunk(pg_db):
    client, calls = _fake_openai_client()

    first_result = ingest_page(
        pg_db, _processed_page(_markdown(_SENTENCE_A)), embedding_client=client
    )
    old_hashes = {
        c.content_hash
        for c in pg_db.scalars(select(Chunk).where(Chunk.page_id == first_result.page_id)).all()
    }
    calls.clear()

    result = ingest_page(
        pg_db, _processed_page(_markdown(_SENTENCE_A_EDITED)), embedding_client=client
    )

    assert result.skipped is False
    assert result.chunks_created == 1  # only Sekcja A's new content
    assert result.chunks_reused == 1  # Sekcja B unchanged, embedding reused
    assert result.chunks_deleted == 1  # old Sekcja A chunk removed
    assert len(calls) == 1
    assert len(calls[0]) == 1  # exactly one text sent for re-embedding

    remaining_chunks = pg_db.scalars(select(Chunk).where(Chunk.page_id == result.page_id)).all()
    assert len(remaining_chunks) == 2
    remaining_hashes = {c.content_hash for c in remaining_chunks}
    removed_hash = old_hashes - remaining_hashes
    assert len(removed_hash) == 1
