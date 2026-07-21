from pathlib import Path

FULL_TEXT_HEADING = "## Full Extracted Text"


def extract_pdf_text(pdf_path: Path) -> str:
    """Convert a PDF to Markdown via tools/pdf_to_md and return only its
    "Full Extracted Text" section — the rest of that tool's output is its own
    LLM analysis (summary/key facts/entities/action items), not raw page
    content, and would pollute embeddings/citations if included."""
    try:
        from pdf_to_md import analyze_pdf
    except ImportError as exc:
        raise RuntimeError(
            "pdf_to_md is not installed. See backend/pyproject.toml for why it isn't "
            "a regular dependency yet, and install it separately to crawl PDF pages."
        ) from exc

    md_path = analyze_pdf(pdf_path)
    full_markdown = md_path.read_text(encoding="utf-8")
    return _extract_full_text_section(full_markdown)


def _extract_full_text_section(markdown: str) -> str:
    start = markdown.find(FULL_TEXT_HEADING)
    if start == -1:
        return markdown.strip()
    section = markdown[start + len(FULL_TEXT_HEADING) :]
    next_heading = section.find("\n## ")
    if next_heading != -1:
        section = section[:next_heading]
    return section.strip()
