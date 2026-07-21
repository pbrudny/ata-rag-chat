from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chunk import Chunk


@dataclass(frozen=True)
class SearchResult:
    chunk: Chunk
    similarity: float


def search_chunks(db: Session, query_embedding: list[float], top_k: int = 5) -> list[SearchResult]:
    """Cosine-similarity search over chunks, most similar first."""
    distance = Chunk.embedding.cosine_distance(query_embedding)
    query = select(Chunk, distance.label("distance")).order_by(distance).limit(top_k)
    rows = db.execute(query).all()
    return [SearchResult(chunk=chunk, similarity=1 - distance) for chunk, distance in rows]
