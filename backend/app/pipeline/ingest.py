from dataclasses import dataclass
from datetime import UTC, datetime

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chunking.chunker import chunk_markdown
from app.core.config import settings
from app.embeddings.embedder import embed_texts
from app.embeddings.hashing import hash_content
from app.models.chunk import Chunk
from app.models.page import Page
from app.pipeline.crawl_page import ProcessedPage


@dataclass(frozen=True)
class IngestResult:
    page_id: object
    skipped: bool
    chunks_created: int
    chunks_reused: int
    chunks_deleted: int


def ingest_page(
    db: Session, processed: ProcessedPage, *, embedding_client: OpenAI | None = None
) -> IngestResult:
    """Incrementally ingest a crawled page: skip entirely if the page's
    content is unchanged, otherwise re-chunk and re-embed only the chunks
    whose content actually changed, and clean up chunks no longer present."""
    page = db.scalar(select(Page).where(Page.url == processed.url))
    now = datetime.now(UTC)

    if page is not None and page.content_hash == processed.content_hash:
        page.last_crawled_at = now
        page.http_status = processed.http_status
        page.status = "active"
        page.consecutive_miss_count = 0
        db.commit()
        return IngestResult(
            page.id, skipped=True, chunks_created=0, chunks_reused=0, chunks_deleted=0
        )

    if page is None:
        page = Page(
            url=processed.url,
            title=processed.title,
            source_type=processed.source_type,
            language=processed.language,
            content_hash=processed.content_hash,
            last_crawled_at=now,
            status="active",
            http_status=processed.http_status,
        )
        db.add(page)
    else:
        page.title = processed.title
        page.source_type = processed.source_type
        page.language = processed.language
        page.content_hash = processed.content_hash
        page.last_crawled_at = now
        page.http_status = processed.http_status
        page.status = "active"
        page.consecutive_miss_count = 0
    db.flush()  # ensure page.id is assigned before chunks reference it

    new_by_hash = {
        hash_content(chunk.text): (index, chunk)
        for index, chunk in enumerate(chunk_markdown(processed.markdown))
    }

    existing_chunks = db.scalars(select(Chunk).where(Chunk.page_id == page.id)).all()
    existing_by_hash = {c.content_hash: c for c in existing_chunks}

    hashes_to_embed = [h for h in new_by_hash if h not in existing_by_hash]
    texts_to_embed = [new_by_hash[h][1].text for h in hashes_to_embed]
    embeddings = (
        embed_texts(texts_to_embed, model=settings.embedding_model, client=embedding_client)
        if texts_to_embed
        else []
    )
    embeddings_by_hash = dict(zip(hashes_to_embed, embeddings, strict=True))

    chunks_created = 0
    chunks_reused = 0

    for content_hash, (index, chunk) in new_by_hash.items():
        existing = existing_by_hash.get(content_hash)
        if existing is not None:
            existing.chunk_index = index
            existing.section = chunk.section
            existing.token_count = chunk.token_count
            existing.language = processed.language
            existing.title = processed.title
            chunks_reused += 1
        else:
            db.add(
                Chunk(
                    page_id=page.id,
                    document_id=str(page.id),
                    chunk_index=index,
                    content=chunk.text,
                    content_hash=content_hash,
                    section=chunk.section,
                    token_count=chunk.token_count,
                    language=processed.language,
                    url=processed.url,
                    title=processed.title,
                    source_type=processed.source_type,
                    last_modified=page.last_modified,
                    embedding=embeddings_by_hash[content_hash],
                    embedding_model=settings.embedding_model,
                )
            )
            chunks_created += 1

    stale_hashes = set(existing_by_hash) - set(new_by_hash)
    for stale_hash in stale_hashes:
        db.delete(existing_by_hash[stale_hash])

    db.commit()

    return IngestResult(
        page_id=page.id,
        skipped=False,
        chunks_created=chunks_created,
        chunks_reused=chunks_reused,
        chunks_deleted=len(stale_hashes),
    )
