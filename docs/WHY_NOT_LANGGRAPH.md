# Why Not Just Use LangGraph?

LangGraph is good software. PRIME-SWARM-CORE is not trying to pretend otherwise.

If you want a mature graph runtime backed by the LangChain ecosystem, LangGraph is a strong choice. Use it.

This project exists for a different reason: to own a small, explicit runtime for deep research agents while borrowing proven patterns from the wider ecosystem.

## The Short Comparison

| Question | LangGraph | PRIME-SWARM-CORE |
|---|---|---|
| Main value | Mature state graph runtime | Small owned runtime for research-agent systems |
| Ecosystem | LangChain/LangSmith-centered | Framework-independent |
| Runtime style | Adopt LangGraph primitives | Local `Command`, `RunState`, `GraphRunner` |
| Checkpointing | Built-in ecosystem support | Local protocol plus SQLite implementation |
| Observability | LangSmith-friendly | JSONL, OTEL-shaped spans, optional OTEL adapter |
| Temporal | Not the center of the design | Direct Temporal workflow/activity wrapper |
| Tooling | LangChain-compatible patterns | Typed local `@tool` decorator |
| Structured output | Use ecosystem integrations | Local retry-on-full-signature-validation |
| Philosophy | Use the framework | Steal patterns, own the code |

## When You Should Use LangGraph

Use LangGraph if:

- you already use LangChain or LangSmith
- you want a larger ecosystem now
- you prefer proven framework behavior over owning runtime code
- you need docs, recipes, and community examples immediately
- you do not want to maintain your own orchestration layer

That is a sane choice.

## When PRIME-SWARM-CORE Makes Sense

Use or study PRIME-SWARM-CORE if:

- you want to understand and own the full runtime
- you want a small codebase that can be deleted or reshaped quickly
- you need explicit SQLite checkpointing and local testability
- you want Temporal as a first-class production path
- you are building a deep research agent and want source ranking, debate, roles, retrieval, signatures, and tracing in one minimal foundation
- you do not want orchestration coupled to a large framework dependency graph

## What This Runtime Does Differently

PRIME-SWARM-CORE keeps the core ideas separate:

- graph execution is in `GraphRunner`
- checkpointing is a protocol with SQLite implementation
- tracing is exportable JSONL/OTEL-shaped data
- LLM calls are adapters
- signatures are prompt contracts
- roles, debate, handoffs, and plugins are small independent modules
- Temporal is a direct wrapper, not a future dream

The result is less magic and more wiring. That is the point.

## Tradeoffs

This project is smaller and newer. It does not have LangGraph's ecosystem, documentation depth, hosted observability, or community battle testing.

In exchange, it is easier to read, easier to adapt, easier to test locally, and easier to reason about end to end.

## Honest Status

The runtime is real:

- 45 tests pass
- local examples run
- Temporal parity test passes
- Temporal-backed example completed against a real SDK-managed local dev server

The product is not built yet:

- no FastAPI service
- no hosted app
- no auth
- no billing
- no real research UI
- no deployed SaaS

This is the foundation, not the finished house.

