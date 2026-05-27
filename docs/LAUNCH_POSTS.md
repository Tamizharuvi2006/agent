# Launch Posts

Draft copy for publishing PRIME-SWARM-CORE as an open-source runtime.

## Short Pitch

PRIME-SWARM-CORE is a small Python agent runtime that borrows the best ideas from LangGraph, LangChain, LangSmith, DSPy, CrewAI, AutoGen, Temporal, and others without adopting their full runtimes.

It has typed graph commands, SQLite checkpointing, interrupts, structured-output retries, prompt signatures, JSONL tracing, Temporal integration, and 45 tests.

It is not a SaaS or finished research product yet. It is the chassis.

## Show HN Draft

Title:

```text
Show HN: PRIME-SWARM-CORE, a small Python runtime for deep research agents
```

Post:

```text
I built a small Python agent runtime after studying the patterns that keep reappearing across LangGraph, LangChain, LangSmith, DSPy, CrewAI, AutoGen, Temporal, and similar systems.

The rule was: steal patterns, not packages.

What it includes:

- typed Command returns for graph nodes
- SQLite checkpointing with resume
- human interrupts
- fan-out via Send
- JSONL tracing and OTEL-shaped spans
- typed tool schemas
- structured output retry
- prompt signatures
- mock and OpenAI-compatible chat models
- budget tracking
- source ranking
- in-memory and auto-merging retrieval
- roles, debate, handoffs, SOPs
- plugin folder discovery
- Temporal workflow/activity integration

It has 45 tests, 3 runnable examples, a local-to-Temporal parity test, and a Temporal-backed example that completed against the Temporal SDK's local dev server.

What it is not:

- not a SaaS
- not a finished deep research product
- not trying to replace LangGraph for everyone

I built it as the runtime foundation for a deep research agent: something like Perplexity, but traceable, stateful, inspectable, and able to debate its own conclusions.

The main design question I am exploring: how small can an agent runtime stay while still supporting durable execution, observability, validation, and distributed workflows?
```

## Twitter/X Draft

```text
I built PRIME-SWARM-CORE: a small Python runtime for deep research agents.

The rule: steal patterns, not packages.

Borrowed ideas from LangGraph, LangChain, LangSmith, DSPy, CrewAI, AutoGen, Temporal, etc. Reimplemented the useful parts locally.

What works:
- typed graph Command
- SQLite checkpoint/resume
- interrupts
- fan-out
- JSONL tracing
- typed tools
- structured-output retry
- prompt signatures
- mock + OpenAI-compatible LLM adapters
- budget tracking
- Temporal workflow/activity integration
- 45 tests
- live Temporal dev-server proof

Not a SaaS. Not a finished research agent yet.

It is the chassis.
```

## Reddit / LocalLLaMA Draft

```text
I built a small Python runtime for agent workflows after studying the recurring patterns in LangGraph, LangChain, DSPy, CrewAI, AutoGen, Temporal, and similar projects.

The philosophy is "steal patterns, not packages."

It currently has:

- graph runner with typed Command returns
- SQLite checkpointing and resume
- human interrupts
- fan-out
- JSONL/OTEL-shaped tracing
- typed tool schemas
- structured output retries
- prompt signatures
- mock and OpenAI-compatible chat adapters
- budget tracking
- simple retrieval and auto-merging retrieval
- roles/debate/handoffs/SOPs
- Temporal integration with parity test

The repo has 45 tests and examples for simple research, parallel DAG fan-out, HITL resume, and Temporal backend execution.

I am building it as a foundation for a deep research agent, but I am sharing the runtime first because I think other agent builders may have useful feedback before the product layer gets too opinionated.

Things I would especially like feedback on:

- Is the runtime too small, or still too big?
- Would you use a local-first runtime with direct Temporal support?
- What would make the examples more convincing?
- Where do you think framework lock-in is actually worth it?
```

## Maintainer Note

Do not oversell it as a finished research agent or deployed SaaS. The honest claim is stronger:

> A production-shaped runtime foundation for deep research agents, with local and Temporal execution proven.

