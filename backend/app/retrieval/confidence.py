from dataclasses import dataclass

from app.retrieval.vector_search import SearchResult


@dataclass(frozen=True)
class ConfidenceResult:
    score: float
    top_similarity: float
    mean_similarity: float
    margin: float


def compute_confidence(results: list[SearchResult]) -> ConfidenceResult:
    """Confidence derived purely from retrieval similarity scores: top-1
    similarity dominates, mean similarity rewards broadly relevant results,
    and the margin over the runner-up penalizes ambiguous retrieval."""
    if not results:
        return ConfidenceResult(score=0.0, top_similarity=0.0, mean_similarity=0.0, margin=0.0)

    similarities = [r.similarity for r in results]
    top = similarities[0]
    mean = sum(similarities) / len(similarities)
    margin = top - similarities[1] if len(similarities) > 1 else top

    score = 0.6 * top + 0.3 * mean + 0.1 * min(margin * 2, 1.0)
    score = max(0.0, min(1.0, score))
    return ConfidenceResult(score=score, top_similarity=top, mean_similarity=mean, margin=margin)


def should_answer(confidence: ConfidenceResult, threshold: float) -> bool:
    return confidence.score >= threshold
