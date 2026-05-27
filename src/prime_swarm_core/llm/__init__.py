"""LLM helper primitives."""

from prime_swarm_core.llm.budget import BudgetRecord, BudgetTracker
from prime_swarm_core.llm.chat import AnthropicMessagesChatModel, ChatModel, OpenAICompatibleChatModel
from prime_swarm_core.llm.mock import MockChatModel
from prime_swarm_core.llm.providers import LLMProviderError, LLMProviderPreset, PROVIDER_PRESETS, create_chat_model
from prime_swarm_core.llm.signature import call_signature
from prime_swarm_core.llm.structured import StructuredCallFailed, call_structured

__all__ = [
    "AnthropicMessagesChatModel",
    "BudgetRecord",
    "BudgetTracker",
    "ChatModel",
    "LLMProviderError",
    "LLMProviderPreset",
    "MockChatModel",
    "OpenAICompatibleChatModel",
    "PROVIDER_PRESETS",
    "StructuredCallFailed",
    "call_signature",
    "call_structured",
    "create_chat_model",
]
