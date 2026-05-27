# Agent Share: PRIME-SWARM-CORE v3

Date: 2026-05-27

## Read This First

This workspace is for building `PRIME-SWARM-CORE v3`, an agent orchestration core inspired by the patterns in `HEIST_MANIFEST.md`.

The project rule is simple: learn from major agent frameworks, but do not blindly import their runtimes. Steal patterns, not packages.

## Required Reading

1. `HEIST_MANIFEST.md`
2. `architecture/report/2026-05-27-heist-manifest-research-report.md`
3. Future `docs/HEIST_CREDITS.md` once implementation begins

## Current State

- The workspace contains the manifest, handoff docs, P0, P1, P2, P3 implementation, and tests.
- No git repository was detected at report time.
- The user wants future work to follow the six heist rules exactly.

## Six Heist Rules

1. Steal patterns, not packages.
2. Re-implement in our own style.
3. Credit sources in `docs/HEIST_CREDITS.md`.
4. No abstraction without 3 real use cases.
5. Test our implementation, not frameworks.
6. Delete what does not earn its complexity within 3 months.

## What The Previous Agent Learned

The manifest proposes a selective architecture:

- LangGraph inspires graph state, `Command`, checkpointer, interrupts, subgraphs, streaming.
- LangChain inspires documents, loaders, splitters, retrievers.
- LangSmith inspires traces, eval datasets, evaluator functions.
- CrewAI inspires roles, goals, backstories, task clarity.
- AutoGen inspires group chat and reflection.
- DSPy inspires signatures and eval-driven prompt optimization.
- Pydantic AI inspires typed tools and typed results.
- Instructor inspires retry-on-validation-failure.
- Haystack inspires pipeline naming and branchable typed components.
- LlamaIndex inspires hierarchical retrieval and auto-merging chunks.
- Semantic Kernel inspires plugin folder organization.
- OpenAI Swarm inspires handoffs and stateless agents.
- Agno inspires composable memory, storage, tools, knowledge, sessions, audit.
- Smolagents inspires code-as-action, but only behind a safe feature flag.
- MetaGPT inspires role SOPs and structured role outputs.
- Temporal should be used directly for durable workflows.
- Browser-Use inspires DOM-as-tree browser action input.
- Perplexity/Exa inspires source quality, freshness, highlights, and cite-as-you-go.
- Cursor/Aider inspires plan-then-act and diff-based edits.
- Mastra inspires fluent workflow ergonomics.

## Suggested First Build Scope

P0 foundation has started and currently includes:

- Typed state and `Command`.
- Checkpointer protocol.
- Interrupt/HITL primitive.
- Typed tool decorator.
- Structured output validation retry.
- Document dataclass.
- Local text, JSON, CSV, file-dispatch, and directory loaders.
- Basic splitter/retriever protocols.
- Source ranking heuristics.
- Tests for our local implementation.
- `docs/HEIST_CREDITS.md`.

Validation command used:

```powershell
$env:PYTHONPATH='D:\projects\relyce\agent\src'; & 'C:\Users\aruvi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

Latest result: 10 tests passed.

## P1 State

P1 has started and currently includes:

- LangSmith-style trace spans with events, scores, parent/child context, and OTEL-shaped export dictionaries.
- Eval dataset helpers: `EvalExample`, `EvalResult`, and `evaluate_dataset`.
- Mastra-style fluent workflow specification builder.
- CrewAI-style `Role` dataclass and starter role library.
- AutoGen-style `GroupChat` debate loop with transcript capture.

Validation command:

```powershell
$env:PYTHONPATH='D:\projects\relyce\agent\src'; & 'C:\Users\aruvi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

Latest result: 18 tests passed.

Important caveat: the workflow builder is intentionally only a typed specification builder. It does not execute workflows and does not replace Temporal.

## P2 State

P2 has started and currently includes:

- DSPy-style `Signature` and `FieldSpec` prompt contracts.
- Prompt rendering with input fields, examples, and output JSON schema.
- Output parsing/validation through local type adapters.
- Few-shot bootstrapping through `bootstrap_few_shot`.
- Prompt candidate selection through `optimize_prompt`.
- In-memory keyword retriever for local testing/demos.
- LlamaIndex-style `AutoMergingRetriever`.

Validation command:

```powershell
$env:PYTHONPATH='D:\projects\relyce\agent\src'; & 'C:\Users\aruvi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

Latest result: 24 tests passed.

Important caveat: P2 optimizers are explicit helpers. They do not call an LLM directly and they are not an autonomous training system. The caller supplies the runner, scorer, examples, and candidates.

## P3 State

P3 has started and currently includes:

- OpenAI Swarm-style `Handoff`.
- Agno-style composable `Agent` with role, memory, knowledge, tools, and storage hooks.
- Semantic Kernel-style plugin folder discovery from `schema.json`, `README.md`, and examples.
- MetaGPT-style SOP templates.
- Smolagents-style code-as-action review gate.
- Cursor/Aider-style unified diff helper.

Validation command:

```powershell
$env:PYTHONPATH='D:\projects\relyce\agent\src'; & 'C:\Users\aruvi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

Latest result: 33 tests passed.

Important caveat: code-as-action is review-only and disabled by default. It does not execute generated code.

## Runtime Hardening State

The first runtime hardening pass is implemented:

- Tiny `GraphRunner` that consumes `Command`.
- `SQLiteCheckpointer` with append-only history.
- `JSONLSpanExporter`.
- OpenAI-compatible chat adapter using the Python standard library.
- `call_signature(...)` adapter connecting `Signature` to chat models.
- Local runtime demo in `examples/local_runtime_demo.py`.
- Packaging cleanup through `.gitignore`.

Validation command:

```powershell
$env:PYTHONPATH='D:\projects\relyce\agent\src'; & 'C:\Users\aruvi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

Latest result: 36 tests passed.

Temporal note: `temporalio` is now a required dependency and direct Temporal integration exists through `LocalGraphWorkflow`, `run_local_graph_activity`, and `create_temporal_worker`.

## Runtime Hardening Update

The harder runtime checklist is now partially closed:

- SQLite checkpoint schema uses `(run_id, step_id, state, created_at)` with a `_meta` schema version table.
- SQLite supports `get`, `put`, `list`, and `delete`.
- Graph runner supports resume from checkpoints without re-running completed nodes.
- Graph runner supports `send` fan-out, `max_steps`, and `max_wall_seconds`.
- `GraphLimitExceeded` is raised for guard trips.
- JSONL trace export, multi-export, and a small trace viewer exist.
- Signature calls retry on full signature validation, not just JSON-object parsing.
- Mock chat model and budget tracking exist.
- Determinism helpers exist for replay-safe `now`, `uuid4`, and `random`.
- Examples exist for simple research, parallel fan-out, and HITL resume.

Validation command:

```powershell
$env:PYTHONPATH='D:\projects\relyce\agent\src'; & 'C:\Users\aruvi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

Latest result: 42 tests passed.

Example validation:

```powershell
$env:PYTHONPATH='D:\projects\relyce\agent\src'; & 'C:\Users\aruvi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' examples\01_simple_research.py
$env:PYTHONPATH='D:\projects\relyce\agent\src'; & 'C:\Users\aruvi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' examples\02_parallel_dag.py
$env:PYTHONPATH='D:\projects\relyce\agent\src'; & 'C:\Users\aruvi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' examples\03_hitl_resume.py
```

All three examples completed successfully.

## Do Not Do Yet

- Do not add `langchain` for orchestration.
- Do not build a generic component framework without 3 real components.
- Do not add a workflow DSL before Temporal workflows exist.
- Do not add code-as-action as default behavior.
- Do not import whole frameworks just to copy a simple pattern.

## Handoff Summary

The goal is not speed through imports. The goal is a clean local architecture with borrowed wisdom, clear credit, and tests proving our code works.

For the next implementation pass, the best candidates are a persistent RunStore, HTTP-backed CLI mode, real search/retrieval inside the research graph, or a FastAPI smoke test that starts the app through Uvicorn.

## Public Launch State

Path C was chosen: ship the runtime first, then build the research agent on top.

Public-facing docs were added:

- `README.md`
- `docs/WHY_NOT_LANGGRAPH.md`
- `docs/LAUNCH_POSTS.md`

These docs position the project honestly as a runtime foundation, not a finished deep research product or SaaS.

## Phase 1 Plan State

Phase 1 started after the runtime push.

Plan document:

- `architecture/report/2026-05-27-phase1-api-cli-plan.md`

Scope:

- FastAPI service shell: implemented.
- Typer CLI shell: implemented.
- API key dependency: implemented.
- run create/get schemas: implemented.
- local in-memory run store with Postgres-ready protocol: implemented.
- simple mock-backed research graph exposed through API and CLI: implemented.

Do not claim Postgres, hosted SaaS, or real search/browser tooling until those are actually wired.

Phase 1 validation:

```powershell
$env:PYTHONPATH='D:\projects\relyce\agent\src'; & 'C:\Users\aruvi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

Latest result: 51 tests passed.

## Temporal State

Temporal is now wired directly:

- `temporalio` installed in the bundled runtime and declared as a required dependency.
- `LocalGraphWorkflow` wraps local graph execution as a Temporal workflow.
- `run_local_graph_activity(...)` runs registered graphs through `GraphRunner`.
- `create_temporal_worker(...)` creates a real Temporal `Worker`.
- Parity test verifies the Temporal activity path and local `GraphRunner` produce the same output.
- `examples/01_simple_research.py --backend temporal` runs against the SDK-managed local Temporal dev server and completed successfully.

Latest result: 45 tests passed.

Live Temporal proof command:

```powershell
$env:PYTHONPATH='D:\projects\relyce\agent\src'; & 'C:\Users\aruvi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' examples\01_simple_research.py --backend temporal
```

Result: returned the expected answer, confidence, evidence, question, and sources. The Temporal dev server emitted shutdown warnings during cleanup, but the workflow completed successfully.
