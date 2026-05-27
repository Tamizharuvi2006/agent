"""Provider presets for chat model adapters."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Literal

from prime_swarm_core.llm.budget import BudgetTracker
from prime_swarm_core.llm.chat import AnthropicMessagesChatModel, ChatModel, OpenAICompatibleChatModel, Transport


ProviderKind = Literal["openai", "openrouter", "xai", "grok", "qwen", "dashscope", "anthropic", "claude"]


class LLMProviderError(ValueError):
    """Raised when an LLM provider configuration is not usable."""


@dataclass(frozen=True, slots=True)
class LLMProviderPreset:
    name: str
    adapter: Literal["openai-compatible", "anthropic-messages"]
    base_url: str
    api_key_env: str
    default_model: str
    default_options: dict[str, Any] = field(default_factory=dict)


PROVIDER_PRESETS: dict[str, LLMProviderPreset] = {
    "openai": LLMProviderPreset(
        name="openai",
        adapter="openai-compatible",
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        default_model="gpt-4o-mini",
    ),
    "openrouter": LLMProviderPreset(
        name="openrouter",
        adapter="openai-compatible",
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        default_model="openai/gpt-4o-mini",
    ),
    "xai": LLMProviderPreset(
        name="xai",
        adapter="openai-compatible",
        base_url="https://api.x.ai/v1",
        api_key_env="XAI_API_KEY",
        default_model="grok-4.3",
    ),
    "grok": LLMProviderPreset(
        name="grok",
        adapter="openai-compatible",
        base_url="https://api.x.ai/v1",
        api_key_env="XAI_API_KEY",
        default_model="grok-4.3",
    ),
    "qwen": LLMProviderPreset(
        name="qwen",
        adapter="openai-compatible",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
        default_model="qwen-plus",
    ),
    "dashscope": LLMProviderPreset(
        name="dashscope",
        adapter="openai-compatible",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
        default_model="qwen-plus",
    ),
    "anthropic": LLMProviderPreset(
        name="anthropic",
        adapter="anthropic-messages",
        base_url="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
        default_model="claude-sonnet-4-5",
        default_options={"max_tokens": 1024},
    ),
    "claude": LLMProviderPreset(
        name="claude",
        adapter="anthropic-messages",
        base_url="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
        default_model="claude-sonnet-4-5",
        default_options={"max_tokens": 1024},
    ),
}


def create_chat_model(
    *,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    default_options: dict[str, Any] | None = None,
    budget_tracker: BudgetTracker | None = None,
    transport: Transport | None = None,
) -> ChatModel:
    """Create a chat model from provider presets or explicit settings."""

    provider_name = (provider or os.getenv("PRIME_SWARM_LLM_PROVIDER") or "openai").lower()
    preset = PROVIDER_PRESETS.get(provider_name)
    if preset is None:
        known = ", ".join(sorted(PROVIDER_PRESETS))
        raise LLMProviderError(f"unknown LLM provider '{provider_name}'. known providers: {known}")

    resolved_model = model or os.getenv("PRIME_SWARM_LLM_MODEL") or preset.default_model
    resolved_key = api_key or os.getenv("PRIME_SWARM_LLM_API_KEY") or os.getenv(preset.api_key_env)
    resolved_base_url = base_url or os.getenv("PRIME_SWARM_LLM_BASE_URL") or preset.base_url
    options = {**preset.default_options, **(default_options or {})}

    if preset.adapter == "anthropic-messages":
        return AnthropicMessagesChatModel(
            model=resolved_model,
            api_key=resolved_key,
            base_url=resolved_base_url,
            transport=transport,
            default_options=options,
            budget_tracker=budget_tracker,
        )

    return OpenAICompatibleChatModel(
        model=resolved_model,
        api_key=resolved_key,
        base_url=resolved_base_url,
        transport=transport,
        default_options=options,
        budget_tracker=budget_tracker,
    )
