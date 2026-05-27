"""HITL interrupt and resume with SQLite checkpoints."""

from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from prime_swarm_core.graph import Command, GraphRunner, SQLiteCheckpointer
from prime_swarm_core.tracing import JSONLSpanExporter


def plan_node(state):
    return Command.to("hitl", plan=["search", "extract", "summarize"])


def hitl_node(state):
    if state.values.get("approved"):
        return Command.to("final", approved_plan=state.values["plan"])
    return Command.pause({"plan": state.values["plan"], "question": "Approve plan?"})


def final_node(state):
    return Command.to(None, status_message="approved and resumed")


async def run_example(work_dir: Path) -> dict:
    db_path = work_dir / "hitl.sqlite3"
    runner = GraphRunner(
        {"plan": plan_node, "hitl": hitl_node, "final": final_node},
        checkpointer=SQLiteCheckpointer(db_path),
        trace_exporter=JSONLSpanExporter(work_dir / "hitl.jsonl"),
    )
    interrupted = await runner.run("hitl-demo", start_at="plan")
    resumed = await GraphRunner(
        {"plan": plan_node, "hitl": hitl_node, "final": final_node},
        checkpointer=SQLiteCheckpointer(db_path),
    ).run("hitl-demo", start_at="plan", initial_values={"approved": True})
    return {
        "interrupted": interrupted.interrupted,
        "final_status": resumed.state.status,
        "message": resumed.state.values["status_message"],
    }


async def main() -> None:
    with TemporaryDirectory() as temp_dir:
        print(await run_example(Path(temp_dir)))


if __name__ == "__main__":
    asyncio.run(main())

