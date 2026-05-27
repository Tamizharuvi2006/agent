"""Product-layer services."""

from prime_swarm_core.product.browser import (
    BrowserPage,
    BrowserProvider,
    BrowserProviderError,
    HTTPHTMLBrowserProvider,
    StaticBrowserProvider,
)
from prime_swarm_core.product.research import run_research
from prime_swarm_core.product.runs import InMemoryRunStore, RunRecord, RunStatus, RunStore, SQLiteRunStore
from prime_swarm_core.product.search import (
    HTTPJSONSearchProvider,
    SearchProvider,
    SearchProviderError,
    SearchProviderNotConfigured,
    StaticSearchProvider,
)

__all__ = [
    "HTTPJSONSearchProvider",
    "BrowserPage",
    "BrowserProvider",
    "BrowserProviderError",
    "HTTPHTMLBrowserProvider",
    "InMemoryRunStore",
    "RunRecord",
    "RunStatus",
    "RunStore",
    "SearchProvider",
    "SearchProviderError",
    "SearchProviderNotConfigured",
    "SQLiteRunStore",
    "StaticSearchProvider",
    "StaticBrowserProvider",
    "run_research",
]
