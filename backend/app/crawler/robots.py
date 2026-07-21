from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import httpx


class RobotsChecker:
    def __init__(self, robots_txt: str) -> None:
        self._parser = RobotFileParser()
        self._parser.parse(robots_txt.splitlines())

    @classmethod
    def from_url(cls, base_url: str, client: httpx.Client) -> "RobotsChecker":
        robots_url = urljoin(base_url, "/robots.txt")
        try:
            response = client.get(robots_url, timeout=10)
            text = response.text if response.status_code == 200 else ""
        except httpx.HTTPError:
            text = ""
        return cls(text)

    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        return self._parser.can_fetch(user_agent, url)
