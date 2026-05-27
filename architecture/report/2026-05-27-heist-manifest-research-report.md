# Heist Manifest Research Report

Date: 2026-05-27

## Purpose

This report captures what has been learned from `HEIST_MANIFEST.md` and the follow-up framework research. It is a handoff artifact for future agents so they can understand the project direction before implementing anything.

## Project Goal

Build `PRIME-SWARM-CORE v3`, our own agent orchestration core, by studying strong patterns from major agent frameworks and reimplementing only the parts that fit our codebase.

The project is not to import every framework. The project is to learn from them, rewrite idiomatically, test our own implementation, and delete anything that does not earn its complexity.

## Non-Negotiable Heist Rules

1. Steal patterns, not packages.
2. Re-implement in our own project style.
3. Credit inspirations in `docs/HEIST_CREDITS.md`.
4. No abstraction without 3 real use cases.
5. Test our implementation, not the source frameworks.
6. Delete what does not earn its complexity within 3 months.

## What Was Done

- Read the full `HEIST_MANIFEST.md`.
- Identified the manifest as an architecture blueprint, not implementation code.
- Verified the current workspace only contains the manifest and no implementation yet.
- Researched the current docs for the frameworks and products named in the manifest.
- Summarized the pros, cons, and likely implementation priority.

## Important Workspace State

At the time of this report:

- Workspace path: `D:\projects\relyce\agent`
- Existing project file: `HEIST_MANIFEST.md`
- No git repository was detected in this folder.
- No source implementation exists yet.

## Framework Lessons

| Source | Pattern to learn | Risk to avoid |
|---|---|---|
| LangGraph | Typed state graph, command routing, checkpointing, interrupts, subgraphs, streaming events. | Importing the whole runtime or inheriting LangChain dependency weight. |
| LangChain | Document shape, loaders, splitters, retriever interface, broad integration ideas. | Using chains/agents as the orchestration center. |
| LangSmith | Trace spans, eval datasets, evaluator functions, run metadata, prompt iteration workflow. | SaaS lock-in; prefer OpenTelemetry-compatible boundaries. |
| CrewAI | Role, goal, backstory, task, crew composition, expected output. | Overfitting to sequential crew execution or theatrical role metaphors. |
| AutoGen | GroupChat, speaker manager, reflection loop, uniform conversable agent interface. | Turn-based or heavyweight framework coupling. |
| DSPy | Signatures, eval-backed prompt optimization, few-shot bootstrapping, MIPRO/GEPA-like prompt evolution. | Adding optimizers before stable eval datasets exist. |
| Pydantic AI | Typed tools, typed outputs, validation, dependency patterns, HITL ideas. | Letting its `Agent` abstraction own our architecture. |
| Instructor | Structured output retry with validation feedback. | Importing a dependency for a small pattern we can implement cleanly. |
| Haystack | Pipeline/component naming, typed inputs and outputs, branchable components. | Creating generic component abstractions before 3 use cases. |
| LlamaIndex | Hierarchical retrieval, auto-merging chunks, document/node thinking, query decomposition. | Adopting a heavy query-engine runtime too early. |
| Semantic Kernel | Plugin folder convention, function/plugin boundary, planner/executor separation. | Copying enterprise/C#-centric architecture into Python unnecessarily. |
| OpenAI Swarm | Lightweight handoff primitive, stateless agents, context passing. | Treating an educational library as production infrastructure. |
| Agno | Memory, storage, tools, knowledge, sessions, RBAC, audit, scheduling as platform concerns. | Building a platform before the core runtime is stable. |
| Smolagents | Code-as-action for loops, conditionals, and data transforms. | Unsafe code execution; must be feature-flagged and sandboxed. |
| MetaGPT | Role-specific SOP prompts and output templates. | Overusing software-company metaphors. |
| Temporal | Durable workflows, activities, signals, queries, replay, heartbeats, cron, continue-as-new. | Violating determinism rules or wrapping Temporal before understanding it. |
| Browser-Use | DOM-as-tree with stable element IDs for browser agents. | Outsourcing browser execution or relying on brittle selectors. |
| Perplexity / Exa | Source quality, freshness ranking, highlights, cite-as-you-go behavior. | Depending on opaque ranking magic instead of transparent heuristics. |
| Cursor / Aider | Plan/act loop, diff-based edits, repo-aware context, test-fix workflow. | Coupling runtime design to an IDE or editor. |
| Mastra | Fluent workflow API, agent/workflow/eval product ergonomics. | Copying TypeScript framework structure into a Python core. |

## Recommended Build Order

### P0 Foundation

- `Command` return object for graph nodes.
- Typed run state.
- Checkpointer protocol.
- Interrupt/HITL primitive.
- Typed tool decorator and schema generation.
- Structured-output call with validation retry.
- `Document` dataclass.
- Basic loaders and splitters.
- Retriever protocol.
- Source ranking heuristics.

### P1 Runtime Discipline

- Trace/span model.
- Eval dataset shape.
- Evaluator function interface.
- OpenTelemetry-compatible exporter boundary.
- Temporal workflow integration.
- Minimal workflow readability helpers only after repeated use appears.

### P2 Intelligence Layer

- Role/persona library.
- GroupChat/debate primitive.
- Reflection/revision helper.
- Handoff primitive.
- SOP prompt templates.
- Hierarchical/auto-merging retrieval.

### P3 Advanced Experiments

- DSPy-style prompt optimization.
- Code-as-action execution mode.
- Plugin folder convention.
- Diff-based report revision UX.
- Browser DOM-tree action format.

## Implementation Warnings

- Do not add `langchain` for orchestration.
- Do not build a generic `Component` class until at least 3 components need it.
- Do not create a fluent workflow DSL before real Temporal workflows exist.
- Do not make code execution a default behavior.
- Do not claim framework behavior is tested; only our implementation can be tested.
- Every borrowed pattern should have a small local test and a removal path.

## Source Links Used For Research

- LangChain and LangGraph overview: https://docs.langchain.com/oss/python/langchain/overview
- LangSmith: https://docs.langchain.com/langsmith/home
- CrewAI: https://docs.crewai.com/
- AutoGen: https://microsoft.github.io/autogen/stable/
- DSPy: https://dspy.ai/
- Pydantic AI: https://pydantic.dev/docs/ai/overview/
- Instructor: https://python.useinstructor.com/
- Haystack: https://docs.haystack.deepset.ai/docs/intro
- LlamaIndex: https://developers.llamaindex.ai/python/framework/
- Semantic Kernel: https://learn.microsoft.com/en-us/semantic-kernel/overview/
- OpenAI Swarm: https://github.com/openai/swarm
- Temporal: https://docs.temporal.io/
- Browser-Use: https://docs.browser-use.com/
- Exa: https://exa.ai/docs/reference/search-api-guide
- Agno: https://docs.agno.com/
- Smolagents: https://huggingface.co/docs/smolagents/index
- MetaGPT: https://docs.deepwisdom.ai/main/en/
- Aider: https://aider.chat/docs/
- Mastra: https://mastra.ai/docs

## Next Agent Instructions

Before coding, read:

1. `HEIST_MANIFEST.md`
2. `AGENTSHARE.md`
3. This report

Then start with P0 only. Keep every implementation small, typed, tested, and credited.
