# Phase 1 Local Retrieval Plan

Date: 2026-05-27

## Goal

Replace the research graph's mock-only evidence step with a real local retrieval path.

The product should be able to answer from local files or directories using the existing heist primitives:

- local loaders
- splitters
- in-memory keyword retriever
- source metadata

## Scope

- Add local corpus loading for a file or directory.
- Split loaded documents into retrieval chunks.
- Retrieve top matching chunks for the question.
- Feed retrieved evidence into the existing signature-backed summarizer.
- Include source metadata in run results.
- Preserve deterministic mock fallback when no source path is provided.
- Wire source path through API, CLI local mode, and CLI HTTP mode.
- Add tests for local retrieval and HTTP payloads.

## Non-Goals

- No external web search provider yet.
- No browser tool integration yet.
- No vector database yet.
- No Postgres yet.
- No streaming research output yet.

## Done Definition

- Local source-backed research returns evidence from actual files.
- API and CLI can pass a source path.
- Tests prove local retrieval and HTTP payload behavior.
- Full suite passes.
