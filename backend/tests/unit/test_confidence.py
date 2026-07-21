from app.retrieval.confidence import compute_confidence, should_answer
from app.retrieval.vector_search import SearchResult

THRESHOLD = 0.55


def _result(similarity: float) -> SearchResult:
    return SearchResult(chunk=None, similarity=similarity)


def test_no_results_gives_zero_confidence():
    confidence = compute_confidence([])
    assert confidence.score == 0.0
    assert should_answer(confidence, THRESHOLD) is False


def test_high_similarity_results_yield_high_confidence():
    results = [_result(0.92), _result(0.88), _result(0.81)]
    confidence = compute_confidence(results)
    assert confidence.score > THRESHOLD
    assert should_answer(confidence, THRESHOLD) is True


def test_low_similarity_results_yield_low_confidence():
    results = [_result(0.2), _result(0.15), _result(0.1)]
    confidence = compute_confidence(results)
    assert confidence.score < THRESHOLD
    assert should_answer(confidence, THRESHOLD) is False


def test_single_result_uses_top_similarity_as_margin():
    confidence = compute_confidence([_result(0.7)])
    assert confidence.margin == 0.7


def test_score_is_clamped_to_unit_interval():
    confidence = compute_confidence([_result(1.0), _result(1.0)])
    assert confidence.score <= 1.0
