from app.content.language_detect import detect_language

POLISH_TEXT = (
    "Rekrutacja na studia rozpoczyna sie w lipcu. Wymagane dokumenty nalezy "
    "zlozyc w dziekanacie do konca wrzesnia."
)
ENGLISH_TEXT = (
    "Admissions for the new academic year begin in July. Required documents "
    "must be submitted to the Dean's Office by the end of September."
)


def test_detects_polish():
    assert detect_language(POLISH_TEXT) == "pl"


def test_detects_english():
    assert detect_language(ENGLISH_TEXT) == "en"


def test_returns_none_for_empty_text():
    assert detect_language("") is None
    assert detect_language("   ") is None
