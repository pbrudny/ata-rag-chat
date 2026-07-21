from bs4 import BeautifulSoup, Tag

_NOISE_SELECTORS = [
    "nav",
    "header",
    "footer",
    "aside",
    "[role=navigation]",
    "[role=banner]",
    "[role=contentinfo]",
]
_NOISE_KEYWORDS = ("cookie", "consent", "gdpr", "banner", "sidebar", "advert", "breadcrumb")
_CONTENT_SELECTORS = ["main", "article", "[role=main]", "#content", "#main-content", ".content"]


def extract_main_content(html: str) -> tuple[str | None, str]:
    """Strip navigation/header/footer/cookie-banner noise and return
    (page title, main content HTML)."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else None

    for selector in _NOISE_SELECTORS:
        for element in soup.select(selector):
            element.decompose()

    for element in soup.find_all(True):
        identifiers = " ".join(
            filter(None, [element.get("id", ""), " ".join(element.get("class", []))])
        ).lower()
        if any(keyword in identifiers for keyword in _NOISE_KEYWORDS):
            element.decompose()

    content: Tag | None = None
    for selector in _CONTENT_SELECTORS:
        content = soup.select_one(selector)
        if content is not None:
            break
    if content is None:
        content = soup.body or soup

    return title, str(content)
