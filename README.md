# PRIME-SWARM-CORE

An opinionated Python agent runtime that steals the best patterns from modern agent frameworks without inheriting their runtime lock-in.

PRIME-SWARM-CORE is not a chatbot and not a SaaS. It is the runtime foundation for deep research agents: durable state, typed graph commands, validation retries, traceable execution, local and Temporal-backed runs, and small composable primitives for tools, roles, retrieval, debate, handoffs, and prompt optimization.

## Why This Exists

Most serious agent projects eventually rediscover the same ideas:

- state graphs
- checkpointing
- human interrupts
- typed tool schemas
- structured output retry
- trace spans
- eval datasets
- roles and debate
- prompt signatures
- source ranking
- durable workflows

Existing frameworks solve pieces of this, but often bring a full runtime, large dependency graph, or a mental model you have to adopt wholesale.

This project follows one rule:

> Steal patterns, not packages.

The inspirations are credited in [docs/HEIST_CREDITS.md](docs/HEIST_CREDITS.md). The implementation is local, small, tested, and designed to be deleted if a pattern does not earn its complexity.

## Current Status

Phase 0 runtime is honestly closed.

| Area | Status |
|---|---|
| P0-P3 pattern surface | Done |
| Tests | 59 passing |
| SQLite checkpointing | Done |
| Graph runner | Resume, fan-out, interrupts, guards |
| Tracing | JSONL, OTEL-shaped spans, optional OTEL adapter, viewer |
| LLM adapter | OpenAI-compatible chat, mock model, signature retry |
| Temporal | Required dependency, workflow/activity integration, parity test |
| Live Temporal proof | Completed against SDK-managed local Temporal dev server |
| Phase 1 API/CLI | Started: FastAPI shell, API keys, SQLite/local run store, local/HTTP Typer CLI |
| Deep research product | Mock-backed vertical slice only |
| SaaS deployment | Not started |

## Install

```powershell
python -m pip install -e .
```

Run validation from the repository root:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
```

## Quick Start

Run a local graph:

```python
from prime_swarm_core.graph import Command, GraphRunner

def plan(state):
    return Command.to("answer", plan=f"Answer: {state.values['question']}")

def answer(state):
    return Command.to(None, answer=state.values["plan"])

runner = GraphRunner({"plan": plan, "answer": answer})
result = await runner.run(
    "demo-run",
    start_at="plan",
    initial_values={"question": "What is the heist rule?"},
)

print(result.state.values["answer"])
```

Run examples:

```powershell
$env:PYTHONPATH='src'
python examples\01_simple_research.py
python examples\02_parallel_dag.py
python examples\03_hitl_resume.py
```

Run the Temporal-backed example:

```powershell
$env:PYTHONPATH='src'
python examples\01_simple_research.py --backend temporal
```

The Temporal example uses the Temporal Python SDK's managed local dev server.

## What Is Included

Core runtime:

- `Command`, `Send`, `RunState`
- `GraphRunner`
- `InMemoryCheckpointer`
- `SQLiteCheckpointer`
- `HumanInterrupt`
- `JSONLSpanExporter`
- `MultiSpanExporter`
- `OpenTelemetrySpanExporter`
- `OpenAICompatibleChatModel`
- `MockChatModel`
- `BudgetTracker`
- `DeterminismContext`

Agent-building primitives:

- typed `@tool`
- structured output retry
- `Document`
- local loaders and splitters
- retriever protocol
- in-memory keyword retriever
- auto-merging retriever
- source ranking heuristics
- roles and SOPs
- group chat debate loop
- prompt signatures
- few-shot bootstrapping
- prompt candidate optimizer
- handoffs
- plugin folder discovery
- review-only code-as-action gate
- unified diff helper

Temporal:

- `TemporalGraphRequest`
- `TemporalGraphResult`
- `LocalGraphWorkflow`
- `run_local_graph_activity`
- `create_temporal_worker`
- local-to-Temporal parity test

## What Is Not Built Yet

This is not yet a deep research product. The runtime is the chassis, not the car.

Still missing for a product:

- production FastAPI deployment and background worker mode
- CLI config profiles
- production API key management and user auth
- Postgres persistence
- real web/search/browser tools
- knowledge graph
- multi-agent debate wired into product workflows
- eval harness and self-learning loop
- hosted deployment
- billing and user management

Started in Phase 1:

- `GET /health`
- `POST /v1/runs`
- `GET /v1/runs/{run_id}`
- `x-api-key` authentication
- local in-memory or SQLite run store
- `prime-swarm health`
- `prime-swarm research "question"`
- `prime-swarm health --api-url http://127.0.0.1:8000`
- `prime-swarm research "question" --api-url http://127.0.0.1:8000 --api-key dev-key`

The Phase 1 run path is intentionally mock-backed. It proves the public contract before real search, Postgres, and product workflows are added. Set `PRIME_SWARM_RUN_DB` or pass CLI `--db` when local run records should survive process restarts.

## Examples

| Example | Shows |
|---|---|
| [examples/01_simple_research.py](examples/01_simple_research.py) | single research flow, mock LLM, signatures, local and Temporal backend |
| [examples/02_parallel_dag.py](examples/02_parallel_dag.py) | fan-out via `Send` |
| [examples/03_hitl_resume.py](examples/03_hitl_resume.py) | human interrupt and resume from SQLite |
| [examples/local_runtime_demo.py](examples/local_runtime_demo.py) | basic runtime summary |

## Validation

Latest validation:

```text
59 tests passed
```

Live Temporal proof:

```powershell
$env:PYTHONPATH='src'
python examples\01_simple_research.py --backend temporal
```

Result: completed successfully against the SDK-managed local Temporal dev server and returned the expected research output.

## Design Rules

1. Steal patterns, not packages.
2. Re-implement in this codebase's style.
3. Credit inspirations.
4. No abstraction without real use cases.
5. Test this implementation, not the source frameworks.
6. Delete what does not earn its complexity.

## Why Not Just Use LangGraph?

Short version: if LangGraph fits your problem, use it. PRIME-SWARM-CORE exists for teams that want a smaller, local, inspectable runtime with explicit ownership of checkpointing, tracing, tools, validation, and Temporal wiring.

Longer comparison: [docs/WHY_NOT_LANGGRAPH.md](docs/WHY_NOT_LANGGRAPH.md).

## Roadmap

Recommended next path:

1. Publish the runtime as OSS.
2. Build the deep research agent on top.
3. Replace Phase 1 mock research with real search/retrieval.
4. Add Postgres persistence.
5. Add real browser/search/knowledge-graph integrations.
6. Add eval harness and self-learning.

## Phase 1 API

Create the app:

```python
from prime_swarm_core.api import create_app

app = create_app()
```

Run locally:

```powershell
$env:PRIME_SWARM_API_KEY='dev-key'
$env:PRIME_SWARM_RUN_DB='data/runs.sqlite'
uvicorn prime_swarm_core.api.app:app --reload
```

Create a run:

```powershell
curl -X POST http://127.0.0.1:8000/v1/runs `
  -H "x-api-key: dev-key" `
  -H "content-type: application/json" `
  -d "{\"question\":\"What is the heist rule?\"}"
```

CLI:

```powershell
prime-swarm health
prime-swarm research "What is the heist rule?"
prime-swarm research "What is the heist rule?" --json
prime-swarm research "What is the heist rule?" --db data/runs.sqlite --json
prime-swarm health --api-url http://127.0.0.1:8000
prime-swarm research "What is the heist rule?" --api-url http://127.0.0.1:8000 --api-key dev-key --json
```
