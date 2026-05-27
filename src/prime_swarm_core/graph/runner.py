"""Tiny graph runner for local workflows."""

from __future__ import annotations

import inspect
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from prime_swarm_core.graph.checkpointer import Checkpointer, InMemoryCheckpointer
from prime_swarm_core.graph.command import Command, Send
from prime_swarm_core.graph.interrupt import HumanInterrupt
from prime_swarm_core.graph.state import RunState
from prime_swarm_core.tracing.span import TraceExporter, trace


NodeFn = Callable[[RunState], Command | RunState | dict[str, Any] | Awaitable[Command | RunState | dict[str, Any]]]


@dataclass(frozen=True, slots=True)
class GraphRunResult:
    state: RunState
    steps: int
    interrupted: bool = False
    interrupt_payload: dict[str, Any] | None = None


class GraphLimitExceeded(RuntimeError):
    pass


class GraphRunner:
    """A small sequential runner that understands `Command`."""

    def __init__(
        self,
        nodes: dict[str, NodeFn],
        *,
        checkpointer: Checkpointer | None = None,
        trace_exporter: TraceExporter | None = None,
        max_steps: int = 50,
        max_wall_seconds: float = 300,
    ) -> None:
        if not nodes:
            raise ValueError("GraphRunner needs at least one node")
        if max_steps <= 0:
            raise ValueError("max_steps must be positive")
        if max_wall_seconds <= 0:
            raise ValueError("max_wall_seconds must be positive")
        self.nodes = dict(nodes)
        self.checkpointer = checkpointer or InMemoryCheckpointer()
        self.trace_exporter = trace_exporter
        self.max_steps = max_steps
        self.max_wall_seconds = max_wall_seconds

    async def run(
        self,
        run_id: str,
        *,
        start_at: str,
        initial_values: dict[str, Any] | None = None,
    ) -> GraphRunResult:
        if start_at not in self.nodes:
            raise KeyError(f"unknown start node: {start_at}")

        started_at = time.monotonic()
        existing = await self.checkpointer.get(run_id)
        state = _resume_state(existing, initial_values, run_id, start_at)
        if state.current_node is None:
            state = state.at_node(start_at)
        await self.checkpointer.put(run_id, state)

        steps = 0
        while state.current_node is not None:
            if steps >= self.max_steps:
                raise GraphLimitExceeded(f"graph exceeded max_steps={self.max_steps}")
            if time.monotonic() - started_at > self.max_wall_seconds:
                raise GraphLimitExceeded(f"graph exceeded max_wall_seconds={self.max_wall_seconds}")
            node_name = state.current_node
            if node_name not in self.nodes:
                raise KeyError(f"unknown node: {node_name}")

            with trace(
                "graph.node",
                inputs={"run_id": run_id, "node": node_name, "values": state.values},
                metadata={"node": node_name},
                exporter=self.trace_exporter,
            ) as span:
                try:
                    raw_result = self.nodes[node_name](state)
                    result = await raw_result if inspect.isawaitable(raw_result) else raw_result
                    command = _coerce_command(result)
                    span.outputs = {
                        "goto": command.goto,
                        "update": command.update,
                        "interrupt": command.interrupt,
                        "send_count": len(command.send),
                    }
                except HumanInterrupt as exc:
                    state = state.with_status("interrupted").with_update(interrupt=exc.payload)
                    await self.checkpointer.put(run_id, state)
                    span.outputs = {"interrupt": exc.payload}
                    return GraphRunResult(state=state, steps=steps + 1, interrupted=True, interrupt_payload=exc.payload)

            state = state.with_update(**command.update)
            if command.send:
                fanout_results = await self._run_sends(state, command.send, run_id)
                state = state.with_update(fanout=fanout_results)
            if command.interrupt is not None:
                state = state.with_status("interrupted").with_update(interrupt=command.interrupt)
                await self.checkpointer.put(run_id, state)
                return GraphRunResult(state=state, steps=steps + 1, interrupted=True, interrupt_payload=command.interrupt)

            next_node = command.goto
            state = state.at_node(next_node)
            if next_node is None:
                state = state.with_status("done")
            await self.checkpointer.put(run_id, state)
            steps += 1

        return GraphRunResult(state=state, steps=steps)

    async def _run_sends(self, state: RunState, sends: tuple[Send, ...], run_id: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for send in sends:
            if send.target not in self.nodes:
                raise KeyError(f"unknown fan-out node: {send.target}")
            send_state = state.with_update(**send.payload).at_node(send.target)
            with trace(
                "graph.send",
                inputs={"run_id": run_id, "target": send.target, "payload": send.payload},
                metadata={"node": send.target, "fanout": True},
                exporter=self.trace_exporter,
            ) as span:
                raw_result = self.nodes[send.target](send_state)
                result = await raw_result if inspect.isawaitable(raw_result) else raw_result
                command = _coerce_command(result)
                span.outputs = {"update": command.update, "goto": command.goto}
                results.append({"target": send.target, "update": command.update, "goto": command.goto})
        return results


def _coerce_command(result: Command | RunState | dict[str, Any]) -> Command:
    if isinstance(result, Command):
        return result
    if isinstance(result, RunState):
        return Command(goto=result.current_node, update=result.values)
    if isinstance(result, dict):
        return Command.stay(**result)
    raise TypeError(f"unsupported node result: {type(result).__name__}")


def _resume_state(
    existing: RunState | None,
    initial_values: dict[str, Any] | None,
    run_id: str,
    start_at: str,
) -> RunState:
    if existing is None:
        return RunState(run_id=run_id, values=initial_values or {}, current_node=start_at)
    if existing.status == "done":
        return existing
    if initial_values:
        return existing.with_update(**initial_values)
    return existing
