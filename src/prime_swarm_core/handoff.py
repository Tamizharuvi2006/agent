"""OpenAI Swarm-inspired handoff primitive."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Handoff:
    target_agent: str
    context: dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def require_reason(self) -> "Handoff":
        if not self.reason.strip():
            raise ValueError("handoff reason is required")
        return self


def handoff(target_agent: str, *, context: dict[str, Any] | None = None, reason: str = "") -> Handoff:
    return Handoff(target_agent=target_agent, context=context or {}, reason=reason).require_reason()

