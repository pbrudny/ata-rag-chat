import httpx
import respx

from app.crawler.robots import RobotsChecker

ROBOTS_TXT = """\
User-agent: *
Disallow: /login
Disallow: /admin/
Allow: /
"""


def test_disallowed_path_is_blocked():
    checker = RobotsChecker(ROBOTS_TXT)
    assert checker.can_fetch("https://example.com/login") is False
    assert checker.can_fetch("https://example.com/admin/settings") is False


def test_allowed_path_is_permitted():
    checker = RobotsChecker(ROBOTS_TXT)
    assert checker.can_fetch("https://example.com/about") is True


def test_missing_robots_txt_allows_everything():
    checker = RobotsChecker("")
    assert checker.can_fetch("https://example.com/anything") is True


@respx.mock
def test_from_url_fetches_and_parses_robots_txt():
    respx.get("https://example.com/robots.txt").mock(
        return_value=httpx.Response(200, text=ROBOTS_TXT)
    )
    with httpx.Client() as client:
        checker = RobotsChecker.from_url("https://example.com", client)
    assert checker.can_fetch("https://example.com/login") is False
    assert checker.can_fetch("https://example.com/about") is True


@respx.mock
def test_from_url_falls_back_to_allow_all_on_404():
    respx.get("https://example.com/robots.txt").mock(return_value=httpx.Response(404))
    with httpx.Client() as client:
        checker = RobotsChecker.from_url("https://example.com", client)
    assert checker.can_fetch("https://example.com/anything") is True
