# Profile List/Delete Plan

Date: 2026-05-27

## Goal

Complete basic CLI profile management.

Users can already create and use profiles. They should also be able to inspect and remove them.

## Scope

- Add `list_profiles(...)`.
- Add `delete_profile(...)`.
- Add `prime-swarm profile-list`.
- Add `prime-swarm profile-delete NAME`.
- Preserve the JSON config format.
- Add tests for list/delete behavior.

## Non-Goals

- No interactive confirmation prompt.
- No secret redaction beyond showing profile names only in list output.
- No profile rename command.

## Done Definition

- Profiles can be listed.
- Profiles can be deleted.
- Missing delete target gives a clear error.
- Full suite passes.
