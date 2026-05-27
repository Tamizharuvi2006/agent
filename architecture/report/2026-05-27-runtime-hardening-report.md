# Runtime Hardening Report

Date: 2026-05-27

## Summary

Implemented the first runtime hardening pass after P0-P3. The manifest pattern surface is now backed by a small local runtime path: graph execution, durable local checkpointing, JSONL tracing, an OpenAI-compatible chat adapter, signature-to-chat wiring, and an executable demo.

## Files Added

- `.gitignore`
- `examples/local_runtime_demo.py`
- `src/prime_swarm_core/graph/runner.py`
- `src/prime_swarm_core/graph/sqlite_checkpointer.py`
- `src/prime_swarm_core/tracing/exporters.py`
- `src/prime_swarm_core/llm/chat.py`
- `src/prime_swarm_core/llm/signature.py`
- `tests/test_runtime_integration.py`
- `examples/01_simple_research.py`
- `examples/02_parallel_dag.py`
- `examples/03_hitl_resume.py`

## Files Updated

- `pyproject.toml`
- `AGENTSHARE.md`
- `docs/HEIST_CREDITS.md`
- `src/prime_swarm_core/graph/__init__.py`
- `src/prime_swarm_core/tracing/__init__.py`
- `src/prime_swarm_core/llm/__init__.py`

## Implemented Runtime Pieces

| Area | Implementation |
|---|---|
| Graph runner | `GraphRunner` executes named nodes, consumes `Command`, persists checkpoints, handles interrupts, and exports node spans. |
| Runner hardening | Resume from checkpoint, fan-out via `send`, `max_steps`, `max_wall_seconds`, and `GraphLimitExceeded`. |
| Run result | `GraphRunResult` exposes final state, step count, interrupt state, and interrupt payload. |
| SQLite checkpoints | `SQLiteCheckpointer` stores append-only checkpoint history with `(run_id, step_id, state, created_at)` and `_meta.schema_version`. |
| Trace export | `JSONLSpanExporter`, `MultiSpanExporter`, optional `OpenTelemetrySpanExporter`, and `render_trace_tree(...)`. |
| LLM adapter | `OpenAICompatibleChatModel` calls `/chat/completions` using standard-library HTTP, with injectable fake transport for tests. |
| Signature adapter | `call_signature(...)` renders a `Signature`, calls a chat model, retries on full signature validation failure, and parses validated output. |
| Mock LLM | `MockChatModel` for deterministic tests and examples. |
| Budget tracking | `BudgetTracker` records token usage from OpenAI-compatible responses. |
| Determinism | `DeterminismContext` provides replay-safe `now`, `uuid4`, and `random`. |
| Examples | Simple research, parallel fan-out, HITL resume, and the original local runtime demo. |
| Packaging cleanup | `.gitignore` excludes caches, SQLite files, JSONL traces, build artifacts, and virtualenvs. |

## Validation

Command:

```powershell
$env:PYTHONPATH='D:\projects\relyce\agent\src'; & 'C:\Users\aruvi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

Result:

- 42 tests passed.

Examples were also run successfully:

- `examples/01_simple_research.py`
- `examples/02_parallel_dag.py`
- `examples/03_hitl_resume.py`

## Notable Fix

The first runtime test exposed a Windows SQLite file-handle leak during temporary directory cleanup. `SQLiteCheckpointer` now closes every SQLite connection explicitly.

## Temporal Status

Temporal is now a required dependency in `pyproject.toml`.

Active integration:

- `LocalGraphWorkflow`
- `TemporalGraphRequest`
- `TemporalGraphResult`
- `run_local_graph_activity`
- `create_temporal_worker`

The parity test verifies the Temporal activity path and local `GraphRunner` produce identical output for the same graph.

## Suggested Next Work

1. Add CLI entry points for running examples and inspecting checkpoints.
2. Add a direct Temporal worker implementation using the optional `temporalio` dependency.
3. Add richer examples that combine loaders, retrieval, roles, debate, and signatures.
4. Add type checking/linting once project tooling is chosen.
