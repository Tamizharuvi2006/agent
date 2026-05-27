"""Research run records and persistence boundary."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol


RunStatus = str


@dataclass(frozen=True, slots=True)
class RunRecord:
    run_id: str
    question: str
    status: RunStatus
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "question": self.question,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class RunStore(Protocol):
    async def put(self, record: RunRecord) -> None: ...

    async def get(self, run_id: str) -> RunRecord | None: ...


class InMemoryRunStore:
    """Local run store used until Postgres is selected and wired."""

    def __init__(self) -> None:
        self._records: dict[str, RunRecord] = {}

    async def put(self, record: RunRecord) -> None:
        self._records[record.run_id] = deepcopy(record)

    async def get(self, run_id: str) -> RunRecord | None:
        record = self._records.get(run_id)
        return deepcopy(record) if record else None

