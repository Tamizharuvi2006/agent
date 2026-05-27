"""API request and response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class CreateRunRequest(BaseModel):
    question: str = Field(min_length=1)
    source_path: str | None = None
    browser_url: str | None = None
    use_llm: bool = False
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_base_url: str | None = None
    use_web_search: bool = False
    top_k: int = Field(default=4, ge=1, le=20)


class RunResponse(BaseModel):
    run_id: str
    question: str
    status: str
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    created_at: str
    updated_at: str
