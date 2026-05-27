"""Deterministic mock chat model for tests and examples."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Iterator

from prime_swarm_core.llm.chat import Message


@dataclass(slots=True)
class MockChatModel:
    responses: Iterable[str | dict[str, Any]]
    model: str = "mock"
    calls: list[list[Message]] = field(default_factory=list)
    _responses: Iterator[str | dict[str, Any]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._responses = iter(self.responses)

    async def complete(self, messages: list[Message], **options: Any) -> str:
        self.calls.append(messages)
        response = next(self._responses)
        return json.dumps(response) if isinstance(response, dict) else response
