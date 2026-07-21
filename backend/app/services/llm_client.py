from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.core.config import settings

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def stream_answer(
    system_prompt: str,
    user_message: str,
    *,
    model: str | None = None,
    client: AsyncOpenAI | None = None,
) -> AsyncIterator[str]:
    """Stream the LLM's answer token-by-token given the layered system prompt
    (with the untrusted retrieved context already embedded) and the user's
    question."""
    model = model or settings.openai_model
    client = client or _get_client()
    stream = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
