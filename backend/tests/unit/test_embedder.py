from unittest.mock import MagicMock

from app.embeddings.embedder import embed_texts


def _fake_response(vectors: list[list[float]]) -> MagicMock:
    response = MagicMock()
    response.data = [MagicMock(embedding=v) for v in vectors]
    return response


def test_embed_texts_preserves_order():
    client = MagicMock()
    client.embeddings.create.return_value = _fake_response([[0.1, 0.2], [0.3, 0.4]])

    result = embed_texts(["a", "b"], model="text-embedding-3-small", client=client)

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    client.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small", input=["a", "b"]
    )


def test_embed_texts_batches_large_input():
    client = MagicMock()
    client.embeddings.create.side_effect = [
        _fake_response([[float(i)] for i in range(100)]),
        _fake_response([[float(i)] for i in range(100, 150)]),
    ]

    result = embed_texts(["t"] * 150, model="text-embedding-3-small", client=client)

    assert len(result) == 150
    assert client.embeddings.create.call_count == 2


def test_embed_texts_empty_input_makes_no_call():
    client = MagicMock()
    result = embed_texts([], client=client)
    assert result == []
    client.embeddings.create.assert_not_called()
