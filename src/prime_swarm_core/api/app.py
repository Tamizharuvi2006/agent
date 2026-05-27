"""FastAPI app factory."""

from __future__ import annotations

from fastapi import FastAPI

from prime_swarm_core.api.routes import router
from prime_swarm_core.product import InMemoryRunStore, RunStore


def create_app(store: RunStore | None = None) -> FastAPI:
    app = FastAPI(title="PRIME-SWARM-CORE", version="0.1.0")
    app.state.run_store = store or InMemoryRunStore()
    app.include_router(router)
    return app


app = create_app()

