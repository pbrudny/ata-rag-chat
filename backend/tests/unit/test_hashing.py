from app.embeddings.hashing import hash_content


def test_same_content_produces_same_hash():
    text = "Rekrutacja rozpoczyna sie w lipcu."
    assert hash_content(text) == hash_content(text)


def test_different_content_produces_different_hash():
    assert hash_content("Tekst A") != hash_content("Tekst B")


def test_stable_across_leading_trailing_whitespace():
    assert hash_content("  Tekst A  ") == hash_content("Tekst A")


def test_stable_across_trailing_line_whitespace():
    assert hash_content("Linia jeden   \nLinia dwa") == hash_content("Linia jeden\nLinia dwa")


def test_sensitive_to_internal_content_changes():
    a = "Czesne wynosi 5000 PLN."
    b = "Czesne wynosi 6000 PLN."
    assert hash_content(a) != hash_content(b)
