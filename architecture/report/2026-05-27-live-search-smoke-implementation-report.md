# Live Search Smoke Implementation Report

Date: 2026-05-27

## Summary

Added a gated live search smoke test.

The normal suite does not call the network. The live proof can be enabled when a compatible HTTP JSON search endpoint and optional API key are available.

## Files Added

- `tests/test_live_search_smoke.py`

## Files Updated

- `README.md`
- `AGENTSHARE.md`

## Environment

Required:

- `RUN_LIVE_SEARCH_TESTS=1`
- `PRIME_SWARM_SEARCH_URL`

Optional:

- `PRIME_SWARM_SEARCH_API_KEY`

## Validation

Normal command:

```powershell
$env:PYTHONPATH='src'; python -m unittest discover -s tests -v
```

Expected normal result:

- 68 tests discovered.
- Live search smoke skipped unless env vars are set.

Live command:

```powershell
$env:PYTHONPATH='src'; $env:RUN_LIVE_SEARCH_TESTS='1'; $env:PRIME_SWARM_SEARCH_URL='<provider-url>'; $env:PRIME_SWARM_SEARCH_API_KEY='<provider-key>'; python -m unittest tests.test_live_search_smoke -v
```

## Still Not Done

- No live vendor run was executed in this workspace because no provider endpoint/key is configured.
- No browser integration yet.
- No hosted deployment yet.
