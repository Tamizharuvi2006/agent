"""Typed run state for graph execution."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class RunState:
    """Immutable-ish run snapshot stored by checkpointers."""

    run_id: str
    values: dict[str, Any] = field(default_factory=dict)
    current_node: str | None = None
    status: str = "running"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def with_update(self, **values: Any) -> "RunState":
        next_values = dict(self.values)
        next_values.update(values)
        return replace(
            self,
            values=next_values,
            updated_at=datetime.now(timezone.utc),
        )

    def at_node(self, node: str | None) -> "RunState":
        return replace(self, current_node=node, updated_at=datetime.now(timezone.utc))

    def with_status(self, status: str) -> "RunState":
        return replace(self, status=status, updated_at=datetime.now(timezone.utc))

