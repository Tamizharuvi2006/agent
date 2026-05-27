# LLM Provider Integration Report

Date: 2026-05-27

## Goal

Make the research runtime usable with real hosted LLM APIs while keeping deterministic mock mode as the default for tests and local demos.

## Implemented

- Added provider presets through `create_chat_model(...)`.
- Added OpenAI-compatible presets:
  - `openai`
  - `openrouter`
  - `xai`
  - `grok`
  - `qwen`
  - `dashscope`
- Added native Anthropic Messages API adapter:
  - `anthropic`
  - `claude`
- Added `AnthropicMessagesChatModel`.
- Added server-side API fields:
  - `use_llm`
  - `llm_provider`
  - `llm_model`
  - `llm_base_url`
- Added local CLI flags:
  - `--llm`
  - `--llm-provider`
  - `--llm-model`
  - `--llm-base-url`
- Added CLI profile support for LLM settings.
- Added `prime-swarm llm-test` for a one-shot provider check.
- Added API injection support for a `ChatModel` in tests and future app wiring.

## Environment Variables

Generic:

```powershell
$env:PRIME_SWARM_LLM_PROVIDER='openrouter'
$env:PRIME_SWARM_LLM_MODEL='openai/gpt-4o-mini'
$env:PRIME_SWARM_LLM_API_KEY='<key>'
```

Provider-specific keys:

- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`
- `XAI_API_KEY`
- `DASHSCOPE_API_KEY`
- `ANTHROPIC_API_KEY`

## Validation

Focused validation:

```powershell
$env:PYTHONPATH='src'
python -m unittest tests.test_runtime_integration tests.test_phase1_api_cli -v
```

Result:

```text
46 tests passed
```

Full validation:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
```

Result:

```text
84 tests discovered
83 tests passed
1 test skipped
```

## What This Means

The agent can now run with deterministic mock output or a real provider-backed `ChatModel`.

OpenAI-compatible providers share the same `/chat/completions` adapter. Claude uses its native Messages API adapter because pretending it is OpenAI-shaped would hide real integration differences.

## Still Not Done

- No live provider smoke test ran in this workspace because no provider key was configured.
- No streaming support yet.
- No tool-call normalization across vendors yet.
- No multimodal request abstraction yet.
- No per-user secret manager or hosted SaaS auth yet.

## References Checked

- OpenAI Chat Completions API reference.
- Anthropic Messages API examples and response shape.
- xAI Grok chat completions guide.
- Alibaba Cloud DashScope/Qwen OpenAI-compatible chat completions guide.
