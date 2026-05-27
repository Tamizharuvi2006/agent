"""Search provider boundary for product research runs."""

from __future__ import annotations

from datetime import date
from typing import Any, Protocol

import httpx

from prime_swarm_core.quality import SearchResult


class SearchProvider(Protocol):
    async def search(self, query: str, *, k: int = 5) -> list[SearchResult]: ...


class SearchProviderNotConfigured(RuntimeError):
    """Raised when web search is requested without a configured provider."""


class SearchProviderError(RuntimeError):
    """Raised when a configured search provider cannot return usable results."""


class HTTPJSONSearchProvider:
    """Small adapter for HTTP services that return JSON search results.

    Expected response shape:

    ```json
    {
      "results": [
        {"url": "...", "title": "...", "snippet": "...", "score": 0.7}
      ]
    }
    ```

    A bare JSON list with the same item shape is also accepted.
    """

    def __init__(
        self,
        endpoint: str,
        *,
        api_key: str | None = None,
        timeout: float = 20.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.timeout = timeout
        self.transport = transport

    async def search(self, query: str, *, k: int = 5) -> list[SearchResult]:
        headers = {"authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {"query": query, "k": k}
        try:
            async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
                response = await client.post(self.endpoint, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            raise SearchProviderError(f"search provider returned {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise SearchProviderError(str(exc)) from exc
        except ValueError as exc:
            raise SearchProviderError("search provider returned invalid JSON") from exc

        items = data.get("results", data) if isinstance(data, dict) else data
        if not isinstance(items, list):
            raise SearchProviderError("search provider response must contain a results list")
        return [_result_from_item(item) for item in items[:k]]


class StaticSearchProvider:
    """Deterministic provider for tests and examples."""

    def __init__(self, results: list[SearchResult]) -> None:
        self.results = tuple(results)

    async def search(self, query: str, *, k: int = 5) -> list[SearchResult]:
        return list(self.results[:k])


def _result_from_item(item: Any) -> SearchResult:
    if not isinstance(item, dict):
        raise SearchProviderError("search result item must be an object")
    published_date = _parse_date(item.get("published_date"))
    return SearchResult(
        url=str(item.get("url", "")),
        title=str(item.get("title", "")),
        snippet=str(item.get("snippet", "")),
        score=float(item.get("score", 0.0)),
        published_date=published_date,
    )


def _parse_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None
