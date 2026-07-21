from markdownify import markdownify


def html_to_markdown(html: str) -> str:
    """Convert cleaned HTML to Markdown, preserving headings, tables, lists and links."""
    return markdownify(html, heading_style="ATX", bullets="-").strip()
