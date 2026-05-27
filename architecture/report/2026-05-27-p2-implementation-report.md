# P2 Implementation Report

Date: 2026-05-27

## Summary

Implemented the first P2 pass for `PRIME-SWARM-CORE v3`: DSPy-inspired signatures/optimizers and a LlamaIndex-inspired auto-merging retriever. Everything is local, injectable, and tested.

## Files Added

- `src/prime_swarm_core/prompts/signature.py`
- `src/prime_swarm_core/prompts/__init__.py`
- `src/prime_swarm_core/optimizers/bootstrap.py`
- `src/prime_swarm_core/optimizers/mipro.py`
- `src/prime_swarm_core/optimizers/__init__.py`
- `src/prime_swarm_core/retrievers/memory.py`
- `src/prime_swarm_core/retrievers/auto_merging.py`
- `tests/test_p2_primitives.py`

## Implemented P2 Pieces

| Area | Implementation |
|---|---|
| DSPy-style signatures | `FieldSpec` and `Signature` for typed input/output contracts. |
| Prompt rendering | `Signature.render_prompt(...)` includes instruction, inputs, examples, and output JSON schema. |
| Output parsing | `Signature.parse_output(...)` validates output fields through local type adapters. |
| Few-shot bootstrapping | `bootstrap_few_shot(...)` keeps high-scoring examples from a train set. |
| Prompt optimization | `optimize_prompt(...)` evaluates candidate instructions and returns the best scoring candidate. |
| Local retriever | `InMemoryKeywordRetriever` for small demos and tests. |
| Auto-merging retrieval | `AutoMergingRetriever` returns a parent document when enough child chunks from the same parent match. |

## Validation

Command:

```powershell
$env:PYTHONPATH='D:\projects\relyce\agent\src'; & 'C:\Users\aruvi\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```

Result:

- 24 tests passed.

## Important Caveats

- The optimizers do not call LLMs directly. Callers must provide runner and scorer functions.
- Prompt optimization is currently candidate selection, not full MIPRO.
- The in-memory keyword retriever is only a local/testing implementation, not a production search layer.
- Auto-merging relies on `parent_id` metadata on child documents and a parent document map.

## Suggested Next Work

If moving to P3:

1. Add Swarm-style `Handoff`.
2. Add Agno-style composable `Agent` with memory/knowledge/tools/storage mixins.
3. Add Semantic Kernel-style plugin folder loader.
4. Add MetaGPT-style SOP prompt templates.
5. Add Smol Agents-style code-as-action behind a disabled-by-default safe flag.
6. Add Cursor/Aider-style diff helper for report revisions.

