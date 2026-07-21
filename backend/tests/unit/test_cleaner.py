from app.content.cleaner import extract_main_content

SAMPLE_HTML = """
<html>
<head><title>Rekrutacja - AkademiaTA</title></head>
<body>
<div id="cookie-banner">We use cookies. Accept?</div>
<header>Site header with logo</header>
<nav><a href="/">Home</a><a href="/oferta">Oferta</a></nav>
<main>
  <h1>Rekrutacja</h1>
  <p>Aby aplikowac, nalezy zlozyc wymagane dokumenty.</p>
</main>
<aside class="sidebar">Related links</aside>
<footer>Copyright 2026 AkademiaTA</footer>
</body>
</html>
"""


def test_extracts_page_title():
    title, _ = extract_main_content(SAMPLE_HTML)
    assert title == "Rekrutacja - AkademiaTA"


def test_strips_nav_header_footer_and_cookie_banner():
    _, content = extract_main_content(SAMPLE_HTML)
    assert "Site header with logo" not in content
    assert "Copyright 2026" not in content
    assert "We use cookies" not in content
    assert "Related links" not in content


def test_keeps_main_content():
    _, content = extract_main_content(SAMPLE_HTML)
    assert "Rekrutacja" in content
    assert "wymagane dokumenty" in content


def test_falls_back_to_body_when_no_main_landmark():
    html_without_main = """
    <html><body>
    <header>Header</header>
    <p>Just a plain page with no main tag.</p>
    <footer>Footer</footer>
    </body></html>
    """
    _, content = extract_main_content(html_without_main)
    assert "Just a plain page" in content
    assert "Header" not in content
    assert "Footer" not in content
