"""Structured output retry loop."""

from __future__ import annotations

import json
from dataclasses import is_dataclass
from typing import Any, Awaitable, Callable, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T")
Message = dict[str, str]
ModelCall = Callable[[list[Message]], Awaitable[str]]


class StructuredCallFailed(RuntimeError):
    pass


async def call_structured(
    model_call: ModelCall,
    prompt: str,
    output_model: type[T],
    *,
    max_retries: int = 3,
) -> T:
    if max_retries <= 0:
        raise ValueError("max_retries must be positive")

    messages: list[Message] = [{"role": "user", "content": prompt}]
    last_error: Exception | None = None

    for _attempt in range(max_retries):
        raw = await model_call(messages)
        try:
            return _validate_output(raw, output_model)
        except Exception as exc:
            last_error = exc
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your output failed validation:\n"
                        f"{exc}\n\nReturn corrected JSON only."
                    ),
                }
            )

    raise StructuredCallFailed(f"structured call failed after {max_retries} attempts") from last_error


def _validate_output(raw: str, output_model: type[T]) -> T:
    if _is_pydantic_model(output_model):
        return output_model.model_validate_json(raw)  # type: ignore[return-value]

    data = json.loads(raw)
    if is_dataclass(output_model):
        return output_model(**data)  # type: ignore[misc, return-value]
    return data  # type: ignore[return-value]


def _is_pydantic_model(value: Any) -> bool:
    return isinstance(value, type) and issubclass(value, BaseModel)

