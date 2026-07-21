from langdetect import LangDetectException, detect


def detect_language(text: str) -> str | None:
    """Best-effort ISO 639-1 language code for the given text, or None if
    it can't be determined (e.g. empty/too-short input)."""
    if not text or not text.strip():
        return None
    try:
        return detect(text)
    except LangDetectException:
        return None
