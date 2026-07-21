from app.content.sanitizer import sanitize_html

DIRTY_HTML = """
<html>
<head><style>body { color: red; }</style></head>
<body>
<!-- a tracking comment -->
<script>alert('xss')</script>
<p onclick="doEvil()">Click me</p>
<a href="javascript:doEvil()">Bad link</a>
<a href="/oferta">Good link</a>
<p>Legitimate content about tuition fees.</p>
</body>
</html>
"""


def test_strips_script_and_style_tags():
    result = sanitize_html(DIRTY_HTML)
    assert "<script" not in result
    assert "<style" not in result
    assert "alert" not in result


def test_strips_html_comments():
    result = sanitize_html(DIRTY_HTML)
    assert "tracking comment" not in result


def test_strips_event_handler_attributes():
    result = sanitize_html(DIRTY_HTML)
    assert "onclick" not in result


def test_strips_javascript_urls_but_keeps_normal_links():
    result = sanitize_html(DIRTY_HTML)
    assert "javascript:" not in result
    assert '/oferta"' in result


def test_preserves_legitimate_content():
    result = sanitize_html(DIRTY_HTML)
    assert "Legitimate content about tuition fees." in result
