"""Deterministic helpers for workflow-safe code paths."""

from __future__ import annotations

import random as random_module
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID


@dataclass(slots=True)
class DeterminismContext:
    seed: int = 0
    start: datetime = field(default_factory=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc))
    tick_seconds: int = 1
    _random: random_module.Random = field(init=False, repr=False)
    _ticks: int = field(default=0, init=False, repr=False)
    _uuid_counter: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        self._random = random_module.Random(self.seed)
        self._ticks = 0
        self._uuid_counter = 0

    def now(self) -> datetime:
        value = self.start + timedelta(seconds=self._ticks * self.tick_seconds)
        self._ticks += 1
        return value

    def uuid4(self) -> UUID:
        self._uuid_counter += 1
        return UUID(int=self._uuid_counter)

    def random(self) -> float:
        return self._random.random()


_default_context = DeterminismContext()


def now() -> datetime:
    return _default_context.now()


def uuid4() -> UUID:
    return _default_context.uuid4()


def random() -> float:
    return _default_context.random()
