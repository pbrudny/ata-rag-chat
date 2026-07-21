from app.chunking.chunker import MAX_TOKENS, MIN_TOKENS, chunk_markdown, count_tokens

_SENTENCE = (
    "AkademiaTA oferuje szeroki wybor programow studiow dla przyszlych "
    "studentow z Polski i zagranicy. "
)


def _n_token_text(n_tokens: int) -> str:
    text = ""
    while count_tokens(text) < n_tokens:
        text += _SENTENCE
    return text.strip()


def test_single_section_within_target_range_becomes_one_chunk():
    content = _n_token_text(800)
    markdown = f"# Rekrutacja\n\n{content}"

    chunks = chunk_markdown(markdown)

    assert len(chunks) == 1
    assert chunks[0].section == "Rekrutacja"
    assert MIN_TOKENS <= chunks[0].token_count <= MAX_TOKENS + 50


def test_small_sibling_sections_merge():
    markdown = (
        "# Rekrutacja\n\n"
        "## Dokumenty\n\nZlozenie dokumentow jest wymagane.\n\n"
        "## Terminy\n\nTerminy rekrutacji trwaja do wrzesnia.\n\n"
    )

    chunks = chunk_markdown(markdown)

    merged = [c for c in chunks if "Dokumenty" in c.section]
    assert len(merged) == 1
    assert "Zlozenie dokumentow" in merged[0].text
    assert "Terminy rekrutacji" in merged[0].text


def test_nested_heading_breadcrumb():
    markdown = (
        "# Uczelnia\n\n"
        "## Wydzialy\n\n"
        "### Informatyka\n\nOpis wydzialu informatyki z bogata trescia edukacyjna.\n\n"
    )

    chunks = chunk_markdown(markdown)

    info_chunk = next(c for c in chunks if "Opis wydzialu" in c.text)
    assert info_chunk.section == "Uczelnia > Wydzialy > Informatyka"


def test_oversized_section_splits_without_cutting_mid_sentence():
    content = _SENTENCE * 40
    markdown = f"# Oferta\n\n{content.strip()}"

    chunks = chunk_markdown(markdown)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.section == "Oferta"
        assert chunk.token_count <= MAX_TOKENS + 50
        assert chunk.text.strip().endswith(".")


def test_split_chunks_overlap():
    content = _SENTENCE * 40
    markdown = f"# Oferta\n\n{content.strip()}"

    chunks = chunk_markdown(markdown)

    assert len(chunks) > 1
    last_unit_of_first_chunk = chunks[0].text.strip().split("\n\n")[-1]
    assert last_unit_of_first_chunk in chunks[1].text
