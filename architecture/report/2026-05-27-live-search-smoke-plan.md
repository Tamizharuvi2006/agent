# Live Search Smoke Plan

Date: 2026-05-27

## Goal

Add a live-vendor search proof harness without requiring secrets for the normal test suite.

## Scope

- Add a gated live smoke test.
- Require `RUN_LIVE_SEARCH_TESTS=1`.
- Require `PRIME_SWARM_SEARCH_URL`.
- Optionally use `PRIME_SWARM_SEARCH_API_KEY`.
- Call the configured HTTP JSON search endpoint.
- Run a research flow using the live provider.

## Non-Goals

- No checked-in vendor credentials.
- No default live network calls.
- No provider SDK dependency.
- No browser search.

## Done Definition

- Normal full test suite passes with the live test skipped.
- The live test can be enabled with env vars when a real endpoint is available.
- README and `AGENTSHARE.md` explain the command honestly.
