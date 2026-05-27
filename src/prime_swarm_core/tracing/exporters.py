"""Trace exporters."""

from __future__ import annotations

import json
from pathlib import Path

from prime_swarm_core.tracing.span import Span


class JSONLSpanExporter:
    """Append spans as one JSON object per line."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def export(self, span: Span) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(span.to_otel_dict(), sort_keys=True) + "\n")


class MultiSpanExporter:
    def __init__(self, exporters: list) -> None:
        if not exporters:
            raise ValueError("MultiSpanExporter needs at least one exporter")
        self.exporters = tuple(exporters)

    def export(self, span: Span) -> None:
        for exporter in self.exporters:
            exporter.export(span)


class OpenTelemetrySpanExporter:
    """Optional OTEL exporter adapter.

    This class is only active when `opentelemetry-sdk` is installed. Keeping the
    import lazy avoids turning observability into a required dependency.
    """

    def __init__(self) -> None:
        try:
            from opentelemetry import trace as otel_trace
        except ModuleNotFoundError as exc:
            raise RuntimeError("opentelemetry-sdk is not installed") from exc
        self._tracer = otel_trace.get_tracer("prime_swarm_core")

    def export(self, span: Span) -> None:
        with self._tracer.start_as_current_span(span.name) as otel_span:
            payload = span.to_otel_dict()
            for key, value in payload.get("attributes", {}).items():
                otel_span.set_attribute(key, str(value))
