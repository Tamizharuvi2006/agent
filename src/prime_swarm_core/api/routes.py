"""API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from prime_swarm_core.api.auth import require_api_key
from prime_swarm_core.api.schemas import CreateRunRequest, HealthResponse, RunResponse
from prime_swarm_core.llm import ChatModel
from prime_swarm_core.product import BrowserProvider, SearchProvider, RunStore, run_research


router = APIRouter()


def get_store(request: Request) -> RunStore:
    return request.app.state.run_store


def get_search_provider(request: Request) -> SearchProvider | None:
    return request.app.state.search_provider


def get_browser_provider(request: Request) -> BrowserProvider | None:
    return request.app.state.browser_provider


def get_chat_model(request: Request) -> ChatModel | None:
    return request.app.state.chat_model


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@router.post("/v1/runs", response_model=RunResponse, dependencies=[Depends(require_api_key)])
async def create_run(
    payload: CreateRunRequest,
    store: RunStore = Depends(get_store),
    search_provider: SearchProvider | None = Depends(get_search_provider),
    browser_provider: BrowserProvider | None = Depends(get_browser_provider),
    chat_model: ChatModel | None = Depends(get_chat_model),
) -> RunResponse:
    record = await run_research(
        payload.question,
        store,
        source_path=payload.source_path,
        browser_url=payload.browser_url,
        browser_provider=browser_provider,
        search_provider=search_provider,
        chat_model=chat_model,
        use_llm=payload.use_llm,
        llm_provider=payload.llm_provider,
        llm_model=payload.llm_model,
        llm_base_url=payload.llm_base_url,
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
