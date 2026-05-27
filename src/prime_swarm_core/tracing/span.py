"""Small trace/span model with an OpenTelemetry-shaped export boundary."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import TracebackType
from typing import Any, Iterator, Protocol
from uuid import uuid4


_current_span: ContextVar["Span | None"] = ContextVar("current_span", default=None)


@dataclass(frozen=True, slots=True)
class SpanEvent:
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TraceExporter(Protocol):
    def export(self, span: "Span") -> None: ...


class InMemorySpanExporter:
    """Exporter for tests and local development."""

    def __init__(self) -> None:
        self.spans: list[dict[str, Any]] = []

    def export(self, span: "Span") -> None:
        self.spans.append(span.to_otel_dict())


@dataclass(slots=True)
class Span:
    name: str
    inputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    trace_id: str = field(default_factory=lambda: uuid4().hex)
    span_id: str = field(default_factory=lambda: uuid4().hex[:16])
    parent_span_id: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    outputs: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    events: list[SpanEvent] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)
    _token: Token["Span | None"] | None = field(default=None, init=False, repr=False)

    def add_event(self, name: str, **attributes: Any) -> None:
        self.events.append(SpanEvent(name=name, attributes=attributes))

    def add_score(self, name: str, value: float) -> None:
        if not 0 <= value <= 1:
            raise ValueError("score values must be between 0 and 1")
        self.scores[name] = value

    def end(self, *, outputs: dict[str, Any] | None = None, error: BaseException | str | None = None) -> None:
        if self.ended_at is not None:
            return
        self.outputs = outputs or self.outputs
        if error is not None:
            self.error = str(error)
        self.ended_at = datetime.now(timezone.utc)

    def to_otel_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "context": {"trace_id": self.trace_id, "span_id": self.span_id},
            "parent_span_id": self.parent_span_id,
            "start_time": self.started_at.isoformat(),
            "end_time": self.ended_at.isoformat() if self.ended_at else None,
            "attributes": {
                "inputs": self.inputs,
                "outputs": self.outputs,
                "metadata": self.metadata,
                "scores": self.scores,
                "error": self.error,
            },
            "events": [
                {
                    "name": event.name,
                    "timestamp": event.timestamp.isoformat(),
                    "attributes": event.attributes,
                }
                for event in self.events
            ],
        }

    def __enter__(self) -> "Span":
        self._token = _current_span.set(self)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        self.end(error=exc)
        if self._token is not None:
            _current_span.reset(self._token)
        return False


@contextmanager
def trace(
    name: str,
    *,
    inputs: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    exporter: TraceExporter | None = None,
) -> Iterator[Span]:
    parent = _current_span.get()
    span = Span(
        name=name,
        inputs=inputs or {},
        metadata=metadata or {},
        trace_id=parent.trace_id if parent else uuid4().hex,
        parent_span_id=parent.span_id if parent else None,
    )
    token = _current_span.set(span)
    try:
        yield span
    except BaseException as exc:
        span.end(error=exc)
        if exporter:
            exporter.export(span)
        raise
    else:
        span.end()
        if exporter:
            exporter.export(span)
    finally:
        _current_span.reset(token)
