"""FastAPI app factory."""

from __future__ import annotations

import os

from fastapi import FastAPI

from prime_swarm_core.api.routes import router
from prime_swarm_core.product import (
    BrowserProvider,
    HTTPHTMLBrowserProvider,
    HTTPJSONSearchProvider,
    InMemoryRunStore,
    RunStore,
    SearchProvider,
    SQLiteRunStore,
)


def create_app(
    store: RunStore | None = None,
    search_provider: SearchProvider | None = None,
    browser_provider: BrowserProvider | None = None,
) -> FastAPI:
    app = FastAPI(title="PRIME-SWARM-CORE", version="0.1.0")
    app.state.run_store = store or _default_store()
    app.state.search_provider = search_provider or _default_search_provider()
    app.state.browser_provider = browser_provider or HTTPHTMLBrowserProvider()
    app.include_router(router)
    return app


def _default_store() -> RunStore:
    db_path = os.getenv("PRIME_SWARM_RUN_DB")
    if db_path:
        return SQLiteRunStore(db_path)
    return InMemoryRunStore()


def _default_search_provider() -> SearchProvider | None:
    endpoint = os.getenv("PRIME_SWARM_SEARCH_URL")
    if not endpoint:
        return None
    return HTTPJSONSearchProvider(endpoint, api_key=os.getenv("PRIME_SWARM_SEARCH_API_KEY"))


app = create_app()
