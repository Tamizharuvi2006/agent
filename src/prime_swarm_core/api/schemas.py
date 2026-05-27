"""API request and response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class CreateRunRequest(BaseModel):
    question: str = Field(min_length=1)


class RunResponse(BaseModel):
    run_id: str
    question: str
    status: str
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    created_at: str
    updated_at: str

