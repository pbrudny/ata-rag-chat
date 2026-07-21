import hashlib
from dataclasses import dataclass
from pathlib import Path

from app.content.cleaner import extract_main_content
from app.content.language_detect import detect_language
from app.content.markdown_converter import html_to_markdown
from app.content.sanitizer import sanitize_html
from app.crawler.base import RawPage
from app.crawler.pdf_handler import extract_pdf_text


@dataclass(frozen=True)
class ProcessedPage:
    url: str
    title: str | None
    markdown: str
    language: str | None
    source_type: str
    content_hash: str
    http_status: int


def process_html_page(page: RawPage) -> ProcessedPage:
    html = sanitize_html(page.body.decode("utf-8", errors="replace"))
    title, main_html = extract_main_content(html)
    markdown = html_to_markdown(main_html)
    return _build_processed_page(page, title=title, markdown=markdown, source_type="html")


def process_pdf_page(page: RawPage, downloaded_pdf_path: Path) -> ProcessedPage:
    markdown = extract_pdf_text(downloaded_pdf_path)
    return _build_processed_page(page, title=None, markdown=markdown, source_type="pdf")


def _build_processed_page(
    page: RawPage, *, title: str | None, markdown: str, source_type: str
) -> ProcessedPage:
    content_hash = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    return ProcessedPage(
        url=page.url,
        title=title,
        markdown=markdown,
        language=detect_language(markdown),
        source_type=source_type,
        content_hash=content_hash,
        http_status=page.status_code,
    )
