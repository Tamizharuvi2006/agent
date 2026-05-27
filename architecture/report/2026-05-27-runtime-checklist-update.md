# Runtime Checklist Update

Date: 2026-05-27

## Summary

Closed the remaining local runtime gaps from the seven-task hardening checklist, including direct Temporal workflow/activity integration.

## Completed

- SQLite checkpointer schema now uses `run_id`, `step_id`, `state`, and `created_at`.
- SQLite has `_meta.schema_version`.
- SQLite supports `delete(run_id)`.
- Graph runner resumes from latest checkpoint without re-running completed steps.
- Graph runner supports fan-out via `Send`.
- Graph runner has `max_steps`, `max_wall_seconds`, and `GraphLimitExceeded`.
- JSONL exporter exists.
- Multi-exporter exists.
- Optional OTEL exporter adapter exists and fails honestly if OTEL is not installed.
- Trace viewer exists through `render_trace_tree(...)` and `python -m prime_swarm_core.tracing.viewer`.
- Signature calls retry on full output contract validation.
- Mock chat model exists.
- Budget tracking exists.
- Determinism context exists.
- Three example workflows exist and run.
- Temporal workflow/activity integration exists.
- Temporal parity test exists.
- `examples/01_simple_research.py --backend temporal` completed against the SDK-managed local Temporal dev server.

## Validation

Tests:

```powershell
$env:PYTHONPATH='D:\projects\relyce\agent\src'; & 'C:\Users\aruvi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

Result:

- 45 tests passed.

Examples:

- `examples/01_simple_research.py`: completed.
- `examples/02_parallel_dag.py`: completed.
- `examples/03_hitl_resume.py`: completed.

## Temporal Status

`temporalio` is installed in the bundled runtime and declared as a required dependency in `pyproject.toml`.

Implemented:

1. `LocalGraphWorkflow`
2. `run_local_graph_activity`
3. `create_temporal_worker`
4. Parity test proving local `GraphRunner` and Temporal activity execution produce equivalent output.
5. Live local dev-server proof through `examples/01_simple_research.py --backend temporal`.

Next production step is to run against a persistent Temporal server/task queue.
