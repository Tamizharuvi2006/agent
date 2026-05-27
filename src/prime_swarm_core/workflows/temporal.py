"""Direct Temporal integration for local graph execution."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

NodeFn = Callable[[Any], Any]
_GRAPH_REGISTRY: dict[str, dict[str, NodeFn]] = {}


@dataclass(frozen=True, slots=True)
class TemporalGraphRequest:
    graph_name: str
    run_id: str
    start_at: str
    initial_values: dict[str, Any] = field(default_factory=dict)
    sqlite_path: str | None = None
    trace_path: str | None = None
    max_steps: int = 50
    max_wall_seconds: float = 300


@dataclass(frozen=True, slots=True)
class TemporalGraphResult:
    status: str
    values: dict[str, Any]
    steps: int
    interrupted: bool = False
    interrupt_payload: dict[str, Any] | None = None


def register_temporal_graph(name: str, nodes: Mapping[str, NodeFn]) -> None:
    if not nodes:
        raise ValueError("cannot register an empty graph")
    _GRAPH_REGISTRY[name] = dict(nodes)


def clear_temporal_graphs() -> None:
    _GRAPH_REGISTRY.clear()


@activity.defn
async def run_local_graph_activity(request: TemporalGraphRequest) -> TemporalGraphResult:
    from prime_swarm_core.graph.runner import GraphRunner
    from prime_swarm_core.graph.sqlite_checkpointer import SQLiteCheckpointer
    from prime_swarm_core.tracing.exporters import JSONLSpanExporter

    if request.graph_name not in _GRAPH_REGISTRY:
        raise KeyError(f"unknown temporal graph: {request.graph_name}")

    checkpointer = SQLiteCheckpointer(request.sqlite_path or _default_sqlite_path(request.run_id))
    trace_exporter = JSONLSpanExporter(request.trace_path) if request.trace_path else None
    runner = GraphRunner(
        _GRAPH_REGISTRY[request.graph_name],
        checkpointer=checkpointer,
        trace_exporter=trace_exporter,
        max_steps=request.max_steps,
        max_wall_seconds=request.max_wall_seconds,
    )
    result = await runner.run(
        request.run_id,
        start_at=request.start_at,
        initial_values=request.initial_values,
    )
    return TemporalGraphResult(
        status=result.state.status,
        values=result.state.values,
        steps=result.steps,
        interrupted=result.interrupted,
        interrupt_payload=result.interrupt_payload,
    )


@workflow.defn
class LocalGraphWorkflow:
    @workflow.run
    async def run(self, request: TemporalGraphRequest) -> TemporalGraphResult:
        return await workflow.execute_activity(
            run_local_graph_activity,
            request,
            start_to_close_timeout=timedelta(seconds=request.max_wall_seconds + 30),
        )


def create_temporal_worker(client: Client, *, task_queue: str) -> Worker:
    return Worker(
        client,
        task_queue=task_queue,
        workflows=[LocalGraphWorkflow],
        activities=[run_local_graph_activity],
    )


def _default_sqlite_path(run_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in run_id)
    return str(Path.cwd() / f"{safe}.sqlite3")
