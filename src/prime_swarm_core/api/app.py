"""FastAPI app factory."""

from __future__ import annotations

import os

from fastapi import FastAPI

from prime_swarm_core.api.routes import router
from prime_swarm_core.product import InMemoryRunStore, RunStore, SQLiteRunStore


def create_app(store: RunStore | None = None) -> FastAPI:
    app = FastAPI(title="PRIME-SWARM-CORE", version="0.1.0")
    app.state.run_store = store or _default_store()
    app.include_router(router)
    return app


def _default_store() -> RunStore:
    db_path = os.getenv("PRIME_SWARM_RUN_DB")
    if db_path:
        return SQLiteRunStore(db_path)
    return InMemoryRunStore()


app = create_app()
