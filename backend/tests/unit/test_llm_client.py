from unittest.mock import AsyncMock, MagicMock

from app.services.llm_client import stream_answer


class _FakeStream:
    def __init__(self, deltas):
        self._deltas = deltas

    def __aiter__(self):
        return self._gen()

    async def _gen(self):
        for delta in self._deltas:
            chunk = MagicMock()
            chunk.choices = [MagicMock(delta=MagicMock(content=delta))]
            yield chunk


async def test_stream_answer_yields_text_deltas():
    client = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=_FakeStream(["Hello", " world"]))

    deltas = [d async for d in stream_answer("system", "question", model="gpt-5.5", client=client)]

    assert deltas == ["Hello", " world"]
    client.chat.completions.create.assert_called_once()


async def test_stream_answer_skips_empty_deltas():
    client = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=_FakeStream(["Hi", None, "!"]))

    deltas = [d async for d in stream_answer("system", "question", client=client)]

    assert deltas == ["Hi", "!"]
