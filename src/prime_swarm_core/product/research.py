"""Mock-backed research product service."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from prime_swarm_core.graph import Command, GraphRunner
from prime_swarm_core.llm import MockChatModel, call_signature
from prime_swarm_core.product.runs import RunRecord, RunStore
from prime_swarm_core.prompts import FieldSpec, Signature


def _signature() -> Signature:
    return Signature(
        name="research_answer",
        instruction="Answer the research question from the evidence in one sentence.",
        input_fields=(FieldSpec("question", str), FieldSpec("evidence", str),),
        output_fields=(FieldSpec("answer", str), FieldSpec("confidence", float),),
    )


async def run_research(question: str, store: RunStore, *, run_id: str | None = None) -> RunRecord:
    run_id = run_id or uuid4().hex
    created = RunRecord(run_id=run_id, question=question, status="running")
    await store.put(created)

    model = MockChatModel([{"answer": f"Mock research answer for: {question}", "confidence": 0.8}])
    signature = _signature()

    async def search_node(state):
        evidence = [
            f"Official-style source for {state.values['question']}",
            f"Background note for {state.values['question']}",
        ]
        return Command.to("summarize", evidence="\n".join(evidence))

    async def summarize_node(state):
        output = await call_signature(
            model,
            signature,
            question=state.values["question"],
            evidence=state.values["evidence"],
        )
        return Command.to(None, **output)

    try:
        result = await GraphRunner({"search": search_node, "summarize": summarize_node}).run(
            run_id,
            start_at="search",
            initial_values={"question": question},
        )
        completed = replace(
            created,
            status="completed",
            result=result.state.values,
            updated_at=datetime.now(timezone.utc),
        )
        await store.put(completed)
        return completed
    except Exception as exc:
        failed = replace(created, status="failed", error=str(exc), updated_at=datetime.now(timezone.utc))
        await store.put(failed)
        return failed

