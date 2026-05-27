"""Parallel-style fan-out DAG with local send branches."""

from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from prime_swarm_core.graph import Command, GraphRunner, Send, SQLiteCheckpointer
from prime_swarm_core.tracing import JSONLSpanExporter


QUESTIONS = ("market", "competitors", "risks", "moats")


async def plan_node(state):
    sends = [Send("research", {"subquestion": item}) for item in QUESTIONS]
    return Command.fanout(sends, topic=state.values["topic"])


async def research_node(state):
    subquestion = state.values["subquestion"]
    return Command.stay(finding=f"{subquestion}: local mock finding")


async def run_example(work_dir: Path) -> dict:
    runner = GraphRunner(
        {"plan": plan_node, "research": research_node},
        checkpointer=SQLiteCheckpointer(work_dir / "parallel.sqlite3"),
        trace_exporter=JSONLSpanExporter(work_dir / "parallel.jsonl"),
    )
    result = await runner.run("parallel-dag", start_at="plan", initial_values={"topic": "research agent"})
    return result.state.values


async def main() -> None:
    with TemporaryDirectory() as temp_dir:
        print(await run_example(Path(temp_dir)))


if __name__ == "__main__":
    asyncio.run(main())

