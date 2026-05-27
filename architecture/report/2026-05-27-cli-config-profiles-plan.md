# CLI Config Profiles Plan

Date: 2026-05-27

## Goal

Make the CLI easier to use by letting users store repeated options in named profiles.

## Scope

- Add JSON profile loading.
- Support `--profile` and `--config`.
- Profile fields:
  - `api_url`
  - `api_key`
  - `db`
  - `source`
  - `web`
  - `top_k`
- Keep CLI arguments highest priority.
- Keep env vars above profiles for service credentials.
- Add tests for profile-backed health and research commands.

## Non-Goals

- No config writer command yet.
- No secret manager integration.
- No global install assumptions.
- No TOML/YAML dependency.

## Done Definition

- CLI can use named profiles.
- Missing profile gives a clear error.
- Existing CLI behavior remains unchanged.
- Full suite passes.
