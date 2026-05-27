# Browser Integration Plan

Date: 2026-05-27

## Goal

Add the first browser/page-ingestion boundary for research runs.

This should let a research run use a web page as evidence without importing a full browser automation framework.

## Scope

- Add a `BrowserProvider` protocol.
- Add an HTTP HTML page provider.
- Extract readable text and title from HTML.
- Add `browser_url` to API, CLI, HTTP CLI, and config profiles.
- Feed browser evidence into the research graph.
- Add deterministic tests using mocked/static browser providers.

## Non-Goals

- No Playwright automation yet.
- No click/type/browser session state yet.
- No JavaScript-rendered page execution yet.
- No crawling.

## Done Definition

- Browser/page URL evidence can be used by research runs.
- API and CLI can pass `browser_url`.
- Config profiles can store `browser_url`.
- Full suite passes.
