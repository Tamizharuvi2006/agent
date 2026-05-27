# Phase 1 External Web Search Plan

Date: 2026-05-27

## Goal

Add an external web search integration point without binding the project to a search vendor.

The research graph should be able to use web search results as evidence when explicitly requested and configured.

## Scope

- Add a `SearchProvider` protocol.
- Add an HTTP JSON search provider that can wrap a simple search service.
- Reuse existing `SearchResult` and `rerank_sources` heuristics.
- Add `use_web_search` to API and CLI.
- Add env configuration for the API default provider.
- Keep local retrieval and mock fallback unchanged.
- Add mocked tests. Do not require live external network.

## Non-Goals

- No vendor SDK dependency.
- No live web-search test without credentials.
- No browser scraping.
- No crawling.
- No vector database.

## Done Definition

- Web search can be enabled through API/CLI.
- Missing provider is reported honestly.
- HTTP provider is tested with mocked transport.
- Source ranking is applied before evidence construction.
- Full suite passes.
