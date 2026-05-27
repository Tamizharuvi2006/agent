"""Command-style node return values.

Nodes can return a plain state value in early experiments, but `Command` is the
preferred shape once a node needs routing, state updates, interrupts, or fan-out.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Send:
    """Request that the runner sends state to another node."""

    target: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Command:
    """A node's explicit control-plane response."""

    goto: str | None = None
    update: dict[str, Any] = field(default_factory=dict)
    interrupt: dict[str, Any] | None = None
    send: tuple[Send, ...] = ()

    @classmethod
    def stay(cls, **update: Any) -> "Command":
        return cls(update=update)

    @classmethod
    def to(cls, node: str, **update: Any) -> "Command":
        return cls(goto=node, update=update)

    @classmethod
    def pause(cls, payload: dict[str, Any]) -> "Command":
        return cls(interrupt=payload)

    @classmethod
    def fanout(cls, sends: list[Send] | tuple[Send, ...], **update: Any) -> "Command":
        return cls(update=update, send=tuple(sends))

