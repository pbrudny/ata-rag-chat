from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RawPage:
    url: str
    status_code: int
    content_type: str  # "html" | "pdf" | "other"
    body: bytes
    last_modified: str | None = None


class CrawlerBackend(Protocol):
    def fetch(self, url: str) -> RawPage: ...

    def discover_links(self, page: RawPage) -> list[str]: ...
