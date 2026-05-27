"""Connect prompt signatures to chat models."""

from __future__ import annotations

from typing import Any

from prime_swarm_core.llm.chat import ChatModel, Message
from prime_swarm_core.llm.structured import StructuredCallFailed
from prime_swarm_core.prompts.signature import Signature


async def call_signature(
    model: ChatModel,
    signature: Signature,
    *,
    max_retries: int = 3,
    **inputs: Any,
) -> dict[str, Any]:
    if max_retries <= 0:
        raise ValueError("max_retries must be positive")
    prompt = signature.render_prompt(**inputs)
    messages: list[Message] = [{"role": "user", "content": prompt}]
    last_error: Exception | None = None

    for _attempt in range(max_retries):
        raw = await model.complete(messages, response_format={"type": "json_object"})
        try:
            return signature.parse_output(raw)
        except Exception as exc:
            last_error = exc
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your output failed the signature contract:\n"
                        f"{exc}\n\nReturn corrected JSON only."
                    ),
                }
            )

    raise StructuredCallFailed(f"signature call failed after {max_retries} attempts") from last_error
