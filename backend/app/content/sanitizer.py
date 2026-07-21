from bs4 import BeautifulSoup, Comment

_UNSAFE_TAGS = ["script", "style", "noscript"]
_URL_ATTRS = ("href", "src")


def sanitize_html(html: str) -> str:
    """Strip script/style tags, HTML comments, event-handler attributes, and
    javascript: URLs before any content is persisted or indexed."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(_UNSAFE_TAGS):
        tag.decompose()

    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            value = tag.attrs[attr]
            is_event_handler = attr.lower().startswith("on")
            is_js_url = (
                attr.lower() in _URL_ATTRS
                and isinstance(value, str)
                and value.strip().lower().startswith("javascript:")
            )
            if is_event_handler or is_js_url:
                del tag.attrs[attr]

    return str(soup)
