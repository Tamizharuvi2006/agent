"""API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from prime_swarm_core.api.auth import require_api_key
from prime_swarm_core.api.schemas import CreateRunRequest, HealthResponse, RunResponse
from prime_swarm_core.product import BrowserProvider, SearchProvider, RunStore, run_research


router = APIRouter()


def get_store(request: Request) -> RunStore:
    return request.app.state.run_store


def get_search_provider(request: Request) -> SearchProvider | None:
    return request.app.state.search_provider


def get_browser_provider(request: Request) -> BrowserProvider | None:
    return request.app.state.browser_provider


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@router.post("/v1/runs", response_model=RunResponse, dependencies=[Depends(require_api_key)])
async def create_run(
    payload: CreateRunRequest,
    store: RunStore = Depends(get_store),
    search_provider: SearchProvider | None = Depends(get_search_provider),
    browser_provider: BrowserProvider | None = Depends(get_browser_provider),
) -> RunResponse:
    record = await run_research(
        payload.question,
        store,
        source_path=payload.source_path,
        browser_url=payload.browser_url,
        browser_provider=browser_provider,
        search_provider=search_provider,
        use_web_search=payload.use_web_search,
        top_k=payload.top_k,
    )
    return RunResponse(**record.as_dict())


@router.get("/v1/runs/{run_id}", response_model=RunResponse, dependencies=[Depends(require_api_key)])
async def get_run(run_id: str, store: RunStore = Depends(get_store)) -> RunResponse:
    record = await store.get(run_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
    return RunResponse(**record.as_dict())
