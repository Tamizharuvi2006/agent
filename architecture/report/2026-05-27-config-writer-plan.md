# Config Writer Plan

Date: 2026-05-27

## Goal

Finish the CLI profile workflow by adding a command that writes profile entries.

Users should not have to hand-edit JSON just to save common options.

## Scope

- Add `save_profile(...)` to the CLI config module.
- Add `prime-swarm profile-set NAME`.
- Preserve existing config and profiles.
- Create parent directories when needed.
- Support profile fields:
  - `api_url`
  - `api_key`
  - `db`
  - `source`
  - `web`
  - `top_k`
- Add tests for creating and updating profiles.

## Non-Goals

- No secret manager integration.
- No interactive prompts.
- No delete/list profile commands yet.
- No TOML/YAML support.

## Done Definition

- CLI can create a profile config file.
- CLI can update an existing profile without deleting other profiles.
- Saved profiles are loadable by existing research/health commands.
- Full suite passes.
