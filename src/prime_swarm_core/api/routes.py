"""API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from prime_swarm_core.api.auth import require_api_key
from prime_swarm_core.api.schemas import CreateRunRequest, HealthResponse, RunResponse
from prime_swarm_core.product import RunStore, run_research


router = APIRouter()


def get_store(request: Request) -> RunStore:
    return request.app.state.run_store


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@router.post("/v1/runs", response_model=RunResponse, dependencies=[Depends(require_api_key)])
async def create_run(payload: CreateRunRequest, store: RunStore = Depends(get_store)) -> RunResponse:
    record = await run_research(payload.question, store)
    return RunResponse(**record.as_dict())


@router.get("/v1/runs/{run_id}", response_model=RunResponse, dependencies=[Depends(require_api_key)])
async def get_run(run_id: str, store: RunStore = Depends(get_store)) -> RunResponse:
    record = await store.get(run_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
    return RunResponse(**record.as_dict())

