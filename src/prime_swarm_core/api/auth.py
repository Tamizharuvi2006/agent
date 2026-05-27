"""API key authentication."""

from __future__ import annotations

import os

from fastapi import Header, HTTPException, status


def configured_api_key() -> str:
    return os.getenv("PRIME_SWARM_API_KEY") or "dev-key"


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if x_api_key != configured_api_key():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid API key")

