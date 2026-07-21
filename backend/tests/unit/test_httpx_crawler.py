import httpx
import respx

from app.crawler.base import RawPage
from app.crawler.httpx_crawler import HttpxCrawler

ROBOTS_TXT = """\
User-agent: *
Disallow: /admin
"""

HTML_WITH_LINKS = """
<html><body>
<a href="/oferta">Oferta</a>
<a href="/admin/panel">Admin</a>
<a href="https://example.com/kontakt#section">Kontakt</a>
<a href="https://other-site.com/page">External</a>
<a href="mailto:info@example.com">Mail</a>
<a href="javascript:void(0)">JS</a>
<a href="/dokument.pdf">PDF doc</a>
<a href="/oferta">Duplicate</a>
</body></html>
"""


@respx.mock
def test_fetch_detects_html_content_type():
    respx.get("https://example.com/robots.txt").mock(return_value=httpx.Response(404))
    crawler = HttpxCrawler("https://example.com")
    respx.get("https://example.com/page").mock(
        return_value=httpx.Response(
            200, headers={"content-type": "text/html"}, text="<html></html>"
        )
    )
    page = crawler.fetch("https://example.com/page")
    assert page.content_type == "html"
    assert page.status_code == 200


@respx.mock
def test_fetch_detects_pdf_content_type():
    respx.get("https://example.com/robots.txt").mock(return_value=httpx.Response(404))
    crawler = HttpxCrawler("https://example.com")
    respx.get("https://example.com/doc.pdf").mock(
        return_value=httpx.Response(
            200, headers={"content-type": "application/pdf"}, content=b"%PDF-1.4"
        )
    )
    page = crawler.fetch("https://example.com/doc.pdf")
    assert page.content_type == "pdf"


@respx.mock
def test_discover_links_filters_external_denied_and_non_http_links():
    respx.get("https://example.com/robots.txt").mock(
        return_value=httpx.Response(200, text=ROBOTS_TXT)
    )
    crawler = HttpxCrawler("https://example.com")
    raw_page = RawPage(
        url="https://example.com/start",
        status_code=200,
        content_type="html",
        body=HTML_WITH_LINKS.encode("utf-8"),
    )
    links = crawler.discover_links(raw_page)

    assert "https://example.com/oferta" in links
    assert links.count("https://example.com/oferta") == 1  # de-duplicated
    assert "https://example.com/kontakt" in links  # fragment stripped
    assert "https://example.com/dokument.pdf" in links
    assert not any("admin" in link for link in links)  # robots-disallowed
    assert not any("other-site.com" in link for link in links)  # external host
    assert not any(link.startswith("mailto:") for link in links)
    assert not any(link.startswith("javascript:") for link in links)


@respx.mock
def test_is_allowed_respects_deny_patterns():
    respx.get("https://example.com/robots.txt").mock(return_value=httpx.Response(404))
    crawler = HttpxCrawler("https://example.com")
    assert crawler.is_allowed("https://example.com/oferta") is True
    assert crawler.is_allowed("https://example.com/moodle/login") is False
    assert crawler.is_allowed("https://example.com/search?q=x") is False
