"""Simple research workflow with mock tools and mock LLM."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from temporalio.testing import WorkflowEnvironment

from prime_swarm_core.graph import Command, GraphRunner, SQLiteCheckpointer
from prime_swarm_core.llm import MockChatModel, call_signature
from prime_swarm_core.prompts import FieldSpec, Signature
from prime_swarm_core.tracing import JSONLSpanExporter
from prime_swarm_core.workflows import (
    LocalGraphWorkflow,
    TemporalGraphRequest,
    clear_temporal_graphs,
    create_temporal_worker,
    register_temporal_graph,
)


def web_search(query: str) -> list[str]:
    return [f"Official note about {query}", f"Background source for {query}"]


def extract(source: str) -> str:
    return f"Extracted evidence: {source}"


def build_graph():
    model = MockChatModel([{"answer": "Steal patterns, not packages.", "confidence": 0.93}])
    signature = Signature(
        name="summarize",
        instruction="Summarize the evidence in one sentence.",
        input_fields=(FieldSpec("evidence", str),),
        output_fields=(FieldSpec("answer", str), FieldSpec("confidence", float),),
    )

    async def search_node(state):
        sources = web_search(state.values["question"])
        return Command.to("extract", sources=sources)

    async def extract_node(state):
        evidence = "\n".join(extract(source) for source in state.values["sources"])
        return Command.to("summarize", evidence=evidence)

    async def summarize_node(state):
        output = await call_signature(model, signature, evidence=state.values["evidence"])
        return Command.to(None, **output)

    return {"search": search_node, "extract": extract_node, "summarize": summarize_node}


async def run_example(work_dir: Path) -> dict:
    nodes = build_graph()

    runner = GraphRunner(
        nodes,
        checkpointer=SQLiteCheckpointer(work_dir / "simple.sqlite3"),
        trace_exporter=JSONLSpanExporter(work_dir / "simple.jsonl"),
    )
    result = await runner.run("simple-research", start_at="search", initial_values={"question": "the heist rule"})
    return result.state.values


async def run_temporal_example(work_dir: Path) -> dict:
    task_queue = "prime-swarm-simple-research"
    clear_temporal_graphs()
    register_temporal_graph("simple_research", build_graph())

    async with await WorkflowEnvironment.start_local() as env:
        worker = create_temporal_worker(env.client, task_queue=task_queue)
        async with worker:
            result = await env.client.execute_workflow(
                LocalGraphWorkflow.run,
                TemporalGraphRequest(
                    graph_name="simple_research",
                    run_id="simple-research-temporal",
                    start_at="search",
                    initial_values={"question": "the heist rule"},
                    sqlite_path=str(work_dir / "temporal-simple.sqlite3"),
                    trace_path=str(work_dir / "temporal-simple.jsonl"),
                ),
                id="simple-research-workflow",
                task_queue=task_queue,
            )
    clear_temporal_graphs()
    return result.values


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=("local", "temporal"), default="local")
    args = parser.parse_args()

    with TemporaryDirectory() as temp_dir:
        if args.backend == "temporal":
            print(await run_temporal_example(Path(temp_dir)))
        else:
            print(await run_example(Path(temp_dir)))


if __name__ == "__main__":
    asyncio.run(main())
