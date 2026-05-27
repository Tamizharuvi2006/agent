# Phase 1 Live API Smoke Plan

Date: 2026-05-27

## Goal

Prove the Phase 1 API and HTTP CLI work against a real Uvicorn server, not only FastAPI's in-process test client and mocked transports.

## Scope

- Start `create_app(...)` through Uvicorn on a random localhost port.
- Wait for `/health` over real HTTP.
- Create a source-backed run over real HTTP.
- Call `prime-swarm research ... --api-url ...` against the live server.
- Keep the test deterministic and self-contained.

## Non-Goals

- No public hosting.
- No Docker or deployment setup.
- No external web search provider.
- No load testing.

## Done Definition

- Live smoke test passes locally.
- Full test suite passes.
- README and `AGENTSHARE.md` reflect the new proof.
