import asyncio
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI, OpenAI
from sqlalchemy.orm import Session

from app.content.language_detect import detect_language
from app.core.config import settings
from app.core.prompts.system_prompt import (
    SYSTEM_PROMPT,
    build_context_block,
    detect_injection_markers,
)
from app.embeddings.embedder import embed_texts
from app.models.chat_query import ChatQuery
from app.retrieval.confidence import ConfidenceResult, compute_confidence, should_answer
from app.retrieval.vector_search import SearchResult, search_chunks
from app.services.llm_client import stream_answer

logger = logging.getLogger(__name__)

FALLBACK_MESSAGES = {
    "en": "I couldn't find this information on the AkademiaTA website.",
    "pl": "Nie znalazlem tej informacji na stronie internetowej AkademiaTA.",
}


async def stream_chat_response(
    db: Session,
    question: str,
    *,
    embedding_client: OpenAI | None = None,
    llm_client: AsyncOpenAI | None = None,
    top_k: int = 5,
) -> AsyncIterator[dict[str, Any]]:
    """RAG orchestration for one chat turn. Yields SSE-shaped event dicts:
    {"event": "sources"|"token"|"done", "data": ...}."""
    start = time.perf_counter()
    language = detect_language(question) or "en"

    if detect_injection_markers(question):
        logger.warning("Potential prompt injection markers detected in user query")

    results = await asyncio.to_thread(_retrieve, db, question, embedding_client, top_k)
    confidence = compute_confidence(results)

    if not should_answer(confidence, settings.confidence_threshold):
        _log_query(db, question, language, False, confidence, results, start)
        yield {"event": "sources", "data": []}
        yield {"event": "token", "data": FALLBACK_MESSAGES.get(language, FALLBACK_MESSAGES["en"])}
        yield {"event": "done", "data": {"confidence": confidence.score, "answered": False}}
        return

    yield {"event": "sources", "data": [_source(r) for r in results]}

    context_block = build_context_block([r.chunk.content for r in results])
    user_message = f"{context_block}\n\nUser question: {question}"

    async for delta in stream_answer(SYSTEM_PROMPT, user_message, client=llm_client):
        yield {"event": "token", "data": delta}

    _log_query(db, question, language, True, confidence, results, start)
    yield {"event": "done", "data": {"confidence": confidence.score, "answered": True}}


def _retrieve(
    db: Session, question: str, embedding_client: OpenAI | None, top_k: int
) -> list[SearchResult]:
    [query_embedding] = embed_texts([question], client=embedding_client)
    return search_chunks(db, query_embedding, top_k=top_k)


def _source(result: SearchResult) -> dict[str, str | None]:
    return {
        "title": result.chunk.title,
        "url": result.chunk.url,
        "section": result.chunk.section,
    }


def _log_query(
    db: Session,
    question: str,
    language: str,
    answered: bool,
    confidence: ConfidenceResult,
    results: list[SearchResult],
    start: float,
) -> None:
    db.add(
        ChatQuery(
            question=question,
            language=language,
            answer_returned=answered,
            confidence_score=confidence.score,
            top_similarity_score=confidence.top_similarity,
            retrieved_chunk_ids=[str(r.chunk.id) for r in results],
            latency_ms=int((time.perf_counter() - start) * 1000),
        )
    )
    db.commit()
