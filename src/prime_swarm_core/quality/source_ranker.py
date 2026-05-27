"""Transparent source ranking heuristics."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from urllib.parse import urlparse


WHITELIST_SUFFIXES = (".gov", ".edu")
OFFICIAL_HINTS = ("docs.", "developer.", "developers.", "learn.", "support.")
BLACKLIST_FRAGMENTS = (
    "forbes.com/sites/",
    "medium.com/",
    "towardsdatascience.com/",
    "contentfarm",
)


@dataclass(frozen=True, slots=True)
class SearchResult:
    url: str
    title: str
    snippet: str = ""
    score: float = 0.0
    published_date: date | None = None


def rerank_sources(
    results: list[SearchResult],
    *,
    needs_freshness: bool = False,
    today: date | None = None,
    freshness_window_days: int = 90,
) -> list[SearchResult]:
    today = today or date.today()
    scored = [
        replace(result, score=_score(result, needs_freshness, today, freshness_window_days))
        for result in results
    ]
    return sorted(scored, key=lambda item: item.score, reverse=True)


def _score(
    result: SearchResult,
    needs_freshness: bool,
    today: date,
    freshness_window_days: int,
) -> float:
    score = result.score
    url_lower = result.url.lower()
    domain = urlparse(url_lower).netloc

    if domain.endswith(WHITELIST_SUFFIXES):
        score += 0.3
    if any(hint in domain for hint in OFFICIAL_HINTS):
        score += 0.15
    if any(fragment in url_lower for fragment in BLACKLIST_FRAGMENTS):
        score -= 0.5
    if needs_freshness:
        if result.published_date is None:
            score -= 0.1
        elif (today - result.published_date).days > freshness_window_days:
            score -= 0.2
        else:
            score += 0.1
    return score

