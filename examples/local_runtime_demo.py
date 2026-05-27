"""Local runtime demo for PRIME-SWARM-CORE.

Run with:
    PYTHONPATH=src python examples/local_runtime_demo.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from prime_swarm_core.graph import Command, GraphRunner, SQLiteCheckpointer
from prime_swarm_core.prompts import FieldSpec, Signature
from prime_swarm_core.tracing import JSONLSpanExporter


def plan_node(state):
    question = state.values["question"]
    return Command.to("answer", plan=f"Answer this carefully: {question}")


def answer_node(state):
    return Command.to(None, answer=f"Draft answer for: {state.values['plan']}")


async def run_demo(work_dir: Path) -> dict:
    db_path = work_dir / "checkpoints.sqlite3"
    trace_path = work_dir / "spans.jsonl"

    runner = GraphRunner(
        {"plan": plan_node, "answer": answer_node},
        checkpointer=SQLiteCheckpointer(db_path),
        trace_exporter=JSONLSpanExporter(trace_path),
    )
    result = await runner.run("demo-run", start_at="plan", initial_values={"question": "What is the heist rule?"})

    signature = Signature(
        name="demo_answer",
        instruction="Answer in one sentence.",
        input_fields=(FieldSpec("question", str),),
        output_fields=(FieldSpec("answer", str), FieldSpec("confidence", float),),
    )

    return {
        "status": result.state.status,
        "answer": result.state.values["answer"],
        "trace_path": str(trace_path),
        "signature_schema": signature.output_schema(),
    }


async def main() -> None:
    with TemporaryDirectory() as temp_dir:
        summary = await run_demo(Path(temp_dir))
        for key, value in summary.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())

