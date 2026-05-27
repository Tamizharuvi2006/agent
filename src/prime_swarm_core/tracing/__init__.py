"""Tracing and evaluation primitives."""

from prime_swarm_core.tracing.evals import EvalExample, EvalResult, evaluate_dataset
from prime_swarm_core.tracing.exporters import JSONLSpanExporter, MultiSpanExporter, OpenTelemetrySpanExporter
from prime_swarm_core.tracing.span import InMemorySpanExporter, Span, SpanEvent, TraceExporter, trace

__all__ = [
    "EvalExample",
    "EvalResult",
    "InMemorySpanExporter",
    "JSONLSpanExporter",
    "MultiSpanExporter",
    "OpenTelemetrySpanExporter",
    "Span",
    "SpanEvent",
    "TraceExporter",
    "evaluate_dataset",
    "trace",
]
