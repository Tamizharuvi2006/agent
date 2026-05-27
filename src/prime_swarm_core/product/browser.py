"""Browser/page ingestion boundary for research runs."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Protocol

import httpx


class BrowserProvider(Protocol):
    async def fetch(self, url: str) -> "BrowserPage": ...


class BrowserProviderError(RuntimeError):
    """Raised when a browser provider cannot return usable page content."""


@dataclass(frozen=True, slots=True)
class BrowserPage:
    url: str
    title: str
    text: str


class HTTPHTMLBrowserProvider:
    """Fetch an HTML page over HTTP and extract readable text."""

    def __init__(
        self,
        *,
        timeout: float = 20.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.timeout = timeout
        self.transport = transport

    async def fetch(self, url: str) -> BrowserPage:
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, transport=self.transport) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise BrowserProviderError(f"browser provider returned {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise BrowserProviderError(str(exc)) from exc

        title, text = extract_html_text(response.text)
        return BrowserPage(url=str(response.url), title=title or str(response.url), text=text)


class StaticBrowserProvider:
    """Deterministic browser provider for tests and examples."""

    def __init__(self, pages: dict[str, BrowserPage]) -> None:
        self.pages = dict(pages)

    async def fetch(self, url: str) -> BrowserPage:
        try:
            return self.pages[url]
        except KeyError as exc:
            raise BrowserProviderError(f"page not found: {url}") from exc


def extract_html_text(html: str) -> tuple[str, str]:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.title.strip(), " ".join(parser.text_parts).strip()


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.text_parts: list[str] = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return
        if self._in_title:
            self.title = f"{self.title} {text}".strip()
        elif self._skip_depth == 0:
            self.text_parts.append(text)
