import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.crawler.base import RawPage
from app.crawler.robots import RobotsChecker

DEFAULT_DENY_PATTERNS = [
    r"/login",
    r"/logowanie",
    r"/wp-admin",
    r"/admin",
    r"/moodle",
    r"/search",
    r"[?&]s=",
]

DEFAULT_USER_AGENT = "AkademiaTA-RAG-Bot/1.0"


class HttpxCrawler:
    def __init__(
        self,
        base_url: str,
        client: httpx.Client | None = None,
        deny_patterns: list[str] | None = None,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.host = urlparse(self.base_url).netloc
        self.user_agent = user_agent
        self.client = client or httpx.Client(
            follow_redirects=True, timeout=15.0, headers={"User-Agent": user_agent}
        )
        self._deny_re = re.compile("|".join(deny_patterns or DEFAULT_DENY_PATTERNS), re.IGNORECASE)
        self.robots = RobotsChecker.from_url(self.base_url, self.client)

    def fetch(self, url: str) -> RawPage:
        response = self.client.get(url)
        content_type_header = response.headers.get("content-type", "")
        if "application/pdf" in content_type_header or url.lower().endswith(".pdf"):
            content_type = "pdf"
        elif "text/html" in content_type_header:
            content_type = "html"
        else:
            content_type = "other"
        return RawPage(
            url=str(response.url),
            status_code=response.status_code,
            content_type=content_type,
            body=response.content,
            last_modified=response.headers.get("last-modified"),
        )

    def discover_links(self, page: RawPage) -> list[str]:
        if page.content_type != "html":
            return []
        soup = BeautifulSoup(page.body, "html.parser")
        links: list[str] = []
        seen: set[str] = set()
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].split("#")[0].strip()
            if not href or href.startswith(("mailto:", "tel:", "javascript:")):
                continue
            absolute = urljoin(page.url, href)
            if absolute in seen or not self.is_allowed(absolute):
                continue
            seen.add(absolute)
            links.append(absolute)
        return links

    def is_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if parsed.netloc and parsed.netloc != self.host:
            return False
        if self._deny_re.search(url):
            return False
        return self.robots.can_fetch(url, self.user_agent)
