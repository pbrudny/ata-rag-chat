import hashlib


def hash_content(text: str) -> str:
    """Stable sha256 hash of chunk content, used to detect unchanged chunks
    across crawls so embeddings are only regenerated when content changes."""
    normalized = "\n".join(line.rstrip() for line in text.strip().splitlines())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
