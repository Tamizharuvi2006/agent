"""Chat model adapters."""

from __future__ import annotations

import asyncio
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol

from prime_swarm_core.llm.budget import BudgetTracker


Message = dict[str, str]
Transport = Callable[[str, dict[str, str], dict[str, Any]], Awaitable[dict[str, Any]]]


class ChatModel(Protocol):
    async def complete(self, messages: list[Message], **options: Any) -> str: ...


@dataclass(frozen=True, slots=True)
class OpenAICompatibleChatModel:
    """Small OpenAI-compatible chat adapter using only the standard library."""

    model: str
    api_key: str | None = None
    base_url: str = "https://api.openai.com/v1"
    transport: Transport | None = None
    default_options: dict[str, Any] = field(default_factory=dict)
    budget_tracker: BudgetTracker | None = None

    async def complete(self, messages: list[Message], **options: Any) -> str:
        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key and self.transport is None:
            raise ValueError("api_key or transport is required")

        payload = {
            "model": self.model,
            "messages": messages,
            **self.default_options,
            **options,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key or ''}",
        }
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        response = await (self.transport(url, headers, payload) if self.transport else _post_json(url, headers, payload))
        if self.budget_tracker is not None:
            usage = response.get("usage", {})
            self.budget_tracker.record(
                model=self.model,
                prompt_tokens=int(usage.get("prompt_tokens", 0)),
                completion_tokens=int(usage.get("completion_tokens", 0)),
                total_tokens=int(usage.get("total_tokens", 0)),
            )
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("chat response did not include choices[0].message.content") from exc


async def _post_json(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    return await asyncio.to_thread(_post_json_sync, url, headers, payload)


def _post_json_sync(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"chat completion failed: HTTP {exc.code}: {body}") from exc
