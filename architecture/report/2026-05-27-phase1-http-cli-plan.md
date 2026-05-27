# Phase 1 HTTP CLI Plan

Date: 2026-05-27

## Goal

Let the CLI call the FastAPI service instead of only running the local mock-backed graph in-process.

This keeps the Phase 1 product surface usable in both modes:

- local mode for fast development
- HTTP mode for a running API service

## Scope

- Add `prime_swarm_core.cli.http_client`.
- Support `prime-swarm health --api-url ...`.
- Support `prime-swarm research ... --api-url ... --api-key ...`.
- Read defaults from `PRIME_SWARM_API_URL` and `PRIME_SWARM_API_KEY`.
- Preserve local CLI behavior when no API URL is set.
- Add transport-mocked CLI tests.
- Update README and `AGENTSHARE.md`.

## Non-Goals

- No live server smoke test in this pass.
- No auth profiles or config file yet.
- No streaming CLI output yet.
- No real search/retrieval yet.

## Done Definition

- Existing local CLI tests still pass.
- HTTP CLI mode is tested without a live server.
- Full suite passes.
