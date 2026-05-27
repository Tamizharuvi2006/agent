# Heist Credits

Date: 2026-05-27

This project follows the `HEIST_MANIFEST.md` rule: steal patterns, not packages. The credits below describe inspiration sources for local implementations. They are not claims that the upstream projects endorse this code.

## P0 Foundation Credits

| Local area | Inspired by | What was borrowed |
|---|---|---|
| `prime_swarm_core.graph` | LangGraph | Typed command-style node returns, checkpointing boundary, interrupt primitive. |
| `prime_swarm_core.tools` | Pydantic AI | Typed tool registration and JSON-schema generation from local Python functions/models. |
| `prime_swarm_core.llm.structured` | Instructor | Retry-on-validation-failure loop for structured LLM output. |
| `prime_swarm_core.data` | LangChain | Simple document shape and text splitting patterns. |
| `prime_swarm_core.retrievers` | LangChain / LlamaIndex | Minimal retriever protocol for future vector, BM25, and hierarchical retrieval implementations. |
| `prime_swarm_core.quality` | Perplexity / Exa style research systems | Transparent source quality and freshness reranking heuristics. |

## P1 Credits

| Local area | Inspired by | What was borrowed |
|---|---|---|
| `prime_swarm_core.tracing` | LangSmith / OpenTelemetry / Phoenix-style observability | Nested spans, events, scores, eval examples, evaluator functions, and an OTEL-shaped export boundary. |
| `prime_swarm_core.workflows` | Mastra | Fluent workflow specification ergonomics. This is only a typed spec builder, not a workflow runtime. |
| `prime_swarm_core.roles` | CrewAI | Role definitions with goal, backstory, tools, model hints, expected output, and SOPs. |
| `prime_swarm_core.debate` | AutoGen | GroupChat-style rotating speakers, transcript capture, and consensus stop marker. |

## P2 Credits

| Local area | Inspired by | What was borrowed |
|---|---|---|
| `prime_swarm_core.prompts` | DSPy | Typed signatures with declared input/output fields, prompt rendering, JSON schema output contracts, and output parsing. |
| `prime_swarm_core.optimizers` | DSPy | Eval-driven few-shot bootstrapping and prompt candidate selection with caller-provided runners/scorers. |
| `prime_swarm_core.retrievers.auto_merging` | LlamaIndex | Auto-merging retrieval: when enough sibling chunks match, return the parent document instead of scattered child chunks. |

## P3 Credits

| Local area | Inspired by | What was borrowed |
|---|---|---|
| `prime_swarm_core.handoff` | OpenAI Swarm | Explicit handoff object with target agent, context, and reason. |
| `prime_swarm_core.agents` | Agno | Composable agent wiring for role, memory, knowledge, tools, and storage. |
| `prime_swarm_core.plugins` | Semantic Kernel | Folder-based plugin discovery using `schema.json`, `README.md`, and examples. |
| `prime_swarm_core.sops` | MetaGPT | Standard operating procedure prompt templates with explicit output format. |
| `prime_swarm_core.code_actions` | Smolagents | Code-as-action review gate. Execution is not implemented and is disabled by default. |
| `prime_swarm_core.diffs` | Cursor / Aider | Unified diff generation for reviewable edits. |

## Guardrails

- No LangChain orchestration dependency is used.
- Framework code was not copied.
- Tests target only our implementation.
- New abstractions should remain removable if they do not earn their complexity.
- The workflow builder does not replace Temporal; it only produces a small typed plan for future execution layers.
- Optimizers do not call models directly; callers provide runners and scorers so eval behavior stays explicit.
- Code-as-action is review-only in this implementation and does not execute generated code.
- Temporal is used directly through `prime_swarm_core.workflows.temporal`; local graph execution is wrapped by a Temporal workflow/activity pair.
