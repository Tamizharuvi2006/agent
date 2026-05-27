# Phase 1 API and CLI Plan

Date: 2026-05-27

## Goal

Start turning the Phase 0 runtime into a usable deep-research product surface without overbuilding the product layer.

Phase 1 should expose the runtime through:

- FastAPI HTTP service
- Typer CLI
- API key authentication
- run creation/status/result schemas
- a persistence boundary that works locally now and can move to Postgres later

## Non-Goals

- No hosted SaaS yet.
- No billing.
- No browser automation yet.
- No knowledge graph yet.
- No real search provider yet.
- No complex UI.
- No fake Postgres integration if Postgres is not present.

## First Vertical Slice

Build a mock-backed research run that proves the public contract:

1. User submits a question over HTTP or CLI.
2. API authenticates with an API key.
3. API creates a run record.
4. Runtime executes a simple research graph.
5. API returns run status and result.
6. CLI can call the same local service or local runner.

## Proposed Package Layout

```text
src/prime_swarm_core/api/
  __init__.py
  app.py
  auth.py
  schemas.py
  routes.py

src/prime_swarm_core/cli/
  __init__.py
  main.py

src/prime_swarm_core/product/
  __init__.py
  research.py
  runs.py
```

## Public API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Service health. |
| `POST` | `/v1/runs` | Create and execute a research run. |
| `GET` | `/v1/runs/{run_id}` | Get run status/result. |

## Authentication

Use a simple API key dependency:

- header: `x-api-key`
- env var: `PRIME_SWARM_API_KEY`
- default local dev key: `dev-key` only when env var is absent

This is not production auth. It is the Phase 1 boundary.

## Persistence

Start with an in-memory `RunStore` and a clear protocol. Do not pretend this is Postgres.

Postgres next step:

- implement the same store protocol using `asyncpg` or SQLAlchemy
- add migration scripts only when a real database target is selected

## CLI

Initial CLI commands:

```powershell
prime-swarm health
prime-swarm research "What is the heist rule?"
```

The CLI should support local execution first. HTTP-backed CLI mode can follow once service deployment exists.

## Validation

Add tests for:

- API health route.
- API key success and failure.
- create run returns completed result.
- get run returns stored result.
- CLI local research command exits cleanly.

## Done Definition

- Phase 1 docs updated before code.
- API/CLI code added.
- Tests pass.
- README/AGENTSHARE mention Phase 1 status.
- Changes committed and pushed.

