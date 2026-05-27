"""Human-in-the-loop interrupt primitive."""

from __future__ import annotations

from typing import Any


class HumanInterrupt(Exception):
    """Raised when execution must pause for human input."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        super().__init__("execution interrupted for human input")


def interrupt(payload: dict[str, Any]) -> None:
    raise HumanInterrupt(payload)

