"""Minimal retrieval protocol."""

from __future__ import annotations

from typing import Protocol

from prime_swarm_core.data.document import Document


class Retriever(Protocol):
    async def retrieve(self, query: str, k: int = 10) -> list[Document]: ...

