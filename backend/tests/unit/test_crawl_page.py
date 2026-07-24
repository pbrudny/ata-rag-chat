import hashlib

from app.crawler.base import RawPage
from app.pipeline.crawl_page import process_html_page

SAMPLE_HTML = b"""
<html>
<head><title>Oferta - AkademiaTA</title></head>
<body>
<nav><a href="/">Home</a></nav>
<script>trackEvent()</script>
<main>
  <h1>Oferta</h1>
  <p onclick="doThing()">Informatyka, Zarzadzanie, Pedagogika.</p>
</main>
<footer>Copyright 2026</footer>
</body>
</html>
"""


def test_process_html_page_produces_clean_markdown_with_hash():
    raw_page = RawPage(
        url="https://akademiata.pl/oferta",
        status_code=200,
        content_type="html",
        body=SAMPLE_HTML,
    )

    result = process_html_page(raw_page)

    assert result.url == "https://akademiata.pl/oferta"
    assert result.title == "Oferta - AkademiaTA"
    assert result.source_type == "html"
    assert result.http_status == 200
    assert "Informatyka" in result.markdown
    assert "Copyright 2026" not in result.markdown
    assert "trackEvent" not in result.markdown
    assert result.content_hash == hashlib.sha256(result.markdown.encode("utf-8")).hexdigest()


def test_process_html_page_strips_nul_bytes():
    raw_page = RawPage(
        url="https://akademiata.pl/oferta",
        status_code=200,
        content_type="html",
        body=b"<html><body><main><p>Informatyka\x00Zarzadzanie</p></main></body></html>",
    )

    result = process_html_page(raw_page)

    assert "\x00" not in result.markdown
    assert "\x00" not in (result.title or "")


def test_process_html_page_is_deterministic_for_unchanged_content():
    raw_page = RawPage(
        url="https://akademiata.pl/oferta",
        status_code=200,
        content_type="html",
        body=SAMPLE_HTML,
    )

    first = process_html_page(raw_page)
    second = process_html_page(raw_page)

    assert first.content_hash == second.content_hash
