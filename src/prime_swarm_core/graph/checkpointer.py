"""Checkpoint persistence boundary."""

from __future__ import annotations

from copy import deepcopy
from typing import Protocol

from prime_swarm_core.graph.state import RunState


class Checkpointer(Protocol):
    async def get(self, run_id: str) -> RunState | None: ...

    async def put(self, run_id: str, state: RunState) -> None: ...

    async def list(self, run_id: str) -> list[RunState]: ...

    async def delete(self, run_id: str) -> None: ...


class InMemoryCheckpointer:
    """Small development checkpointer with history retention."""

    def __init__(self) -> None:
        self._history: dict[str, list[RunState]] = {}

    async def get(self, run_id: str) -> RunState | None:
        history = self._history.get(run_id)
        if not history:
            return None
        return deepcopy(history[-1])

    async def put(self, run_id: str, state: RunState) -> None:
        if state.run_id != run_id:
            raise ValueError("run_id must match state.run_id")
        self._history.setdefault(run_id, []).append(deepcopy(state))

    async def list(self, run_id: str) -> list[RunState]:
        return deepcopy(self._history.get(run_id, []))

    async def delete(self, run_id: str) -> None:
        self._history.pop(run_id, None)
