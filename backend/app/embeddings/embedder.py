from openai import OpenAI

from app.core.config import settings

_BATCH_SIZE = 100

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def embed_texts(
    texts: list[str], *, model: str | None = None, client: OpenAI | None = None
) -> list[list[float]]:
    """Embed a list of texts in batches, preserving input order."""
    if not texts:
        return []
    model = model or settings.embedding_model
    client = client or _get_client()
    embeddings: list[list[float]] = []
    for start in range(0, len(texts), _BATCH_SIZE):
        batch = texts[start : start + _BATCH_SIZE]
        response = client.embeddings.create(model=model, input=batch)
        embeddings.extend(item.embedding for item in response.data)
    return embeddings
