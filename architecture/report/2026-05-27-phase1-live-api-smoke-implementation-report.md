# Phase 1 Live API Smoke Implementation Report

Date: 2026-05-27

## Summary

Added a live Uvicorn smoke test for the Phase 1 product surface.

The test starts a real FastAPI app through Uvicorn on localhost, calls the API over HTTP, and then calls the same server through the HTTP-backed CLI.

## Files Added

- `tests/test_phase1_live_api_smoke.py`

## Files Updated

- `README.md`
- `AGENTSHARE.md`

## Implemented

| Area | Implementation |
|---|---|
| Live server | Uvicorn server in a background thread. |
| Port handling | Random free localhost port. |
| Readiness | Polls `/health` before testing. |
| HTTP API proof | `POST /v1/runs` over real HTTP. |
| HTTP CLI proof | `prime-swarm research ... --api-url ...` against the live server. |
| Source-backed proof | Uses a temporary markdown source file. |

## Validation

Focused command:

```powershell
$env:PYTHONPATH='src'; python -m unittest tests.test_phase1_live_api_smoke -v
```

Result:

- 1 live smoke test passed.

Full-suite expected result after this change:

- 63 tests passing.

## Still Not Done

- No public deployment.
- No Docker smoke.
- No external web search provider.
- No load test.
