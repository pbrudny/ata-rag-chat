from app.content.markdown_converter import html_to_markdown


def test_converts_headings():
    result = html_to_markdown("<h1>Rekrutacja</h1><h2>Wymagania</h2>")
    assert "# Rekrutacja" in result
    assert "## Wymagania" in result


def test_converts_lists():
    result = html_to_markdown("<ul><li>Dowod osobisty</li><li>Swiadectwo maturalne</li></ul>")
    assert "- Dowod osobisty" in result
    assert "- Swiadectwo maturalne" in result


def test_converts_links():
    result = html_to_markdown('<a href="https://akademiata.pl/kontakt">Kontakt</a>')
    assert "[Kontakt](https://akademiata.pl/kontakt)" in result


def test_converts_tables():
    html = """
    <table>
      <tr><th>Program</th><th>Czesne</th></tr>
      <tr><td>Informatyka</td><td>5000 PLN</td></tr>
    </table>
    """
    result = html_to_markdown(html)
    assert "Program" in result
    assert "Czesne" in result
    assert "Informatyka" in result
    assert "|" in result
