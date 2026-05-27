# Phase 1 Persistent RunStore Plan

Date: 2026-05-27

## Goal

Move the Phase 1 product shell beyond in-memory run records without pretending Postgres is already wired.

The next implementation should add a local SQLite-backed `RunStore` that can survive process restarts and keep the same protocol used by the FastAPI routes and CLI.

## Scope

- Add `SQLiteRunStore` under `prime_swarm_core.product`.
- Persist `RunRecord` fields in a small SQLite schema.
- Store `result` as JSON.
- Preserve `created_at` and `updated_at` as timezone-aware ISO timestamps.
- Let `create_app()` choose SQLite when `PRIME_SWARM_RUN_DB` is set.
- Let the CLI use SQLite via a `--db` option.
- Add tests proving restart persistence.
- Update README and `AGENTSHARE.md` with generic paths and honest status.

## Non-Goals

- No Postgres implementation yet.
- No async database driver yet.
- No hosted service or background queue.
- No real web search provider yet.

## Done Definition

- README has no local machine-specific paths.
- SQLite-backed run records survive store recreation.
- API can use SQLite through environment configuration.
- CLI can use SQLite through an explicit option.
- Full test suite passes.
