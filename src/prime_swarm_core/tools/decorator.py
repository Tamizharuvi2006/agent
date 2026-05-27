"""Typed local tool registration.

The decorator records function metadata and a JSON schema without introducing an
agent framework dependency.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable, get_args, get_origin, get_type_hints

from pydantic import BaseModel, TypeAdapter


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    fn: Callable[..., Any]
    schema: dict[str, Any]
    doc: str
    allowed_in: tuple[str, ...]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        fn: Callable[..., Any],
        *,
        name: str | None = None,
        allowed_in: list[str] | tuple[str, ...] | None = None,
    ) -> Callable[..., Any]:
        tool_name = name or fn.__name__
        if tool_name in self._tools:
            raise ValueError(f"tool already registered: {tool_name}")
        self._tools[tool_name] = ToolDefinition(
            name=tool_name,
            fn=fn,
            schema=schema_from_signature(fn),
            doc=inspect.getdoc(fn) or "",
            allowed_in=tuple(allowed_in or ("*",)),
        )
        return fn

    def get(self, name: str) -> ToolDefinition:
        return self._tools[name]

    def list(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def clear(self) -> None:
        self._tools.clear()


default_registry = ToolRegistry()


def tool(
    name: str | None = None,
    *,
    allowed_in: list[str] | tuple[str, ...] | None = None,
    registry: ToolRegistry = default_registry,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        return registry.register(fn, name=name, allowed_in=allowed_in)

    return decorator


def schema_from_signature(fn: Callable[..., Any]) -> dict[str, Any]:
    signature = inspect.signature(fn)
    parameters = list(signature.parameters.values())
    type_hints = get_type_hints(fn)

    if len(parameters) == 1:
        annotation = type_hints.get(parameters[0].name, parameters[0].annotation)
        if _is_pydantic_model(annotation):
            return annotation.model_json_schema()

    properties: dict[str, Any] = {}
    required: list[str] = []
    for parameter in parameters:
        if parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
            raise TypeError("tools cannot use *args or **kwargs")
        annotation = type_hints.get(parameter.name, parameter.annotation)
        if annotation is inspect.Signature.empty:
            raise TypeError(f"tool parameter {parameter.name!r} needs a type annotation")
        properties[parameter.name] = _schema_for_annotation(annotation)
        if parameter.default is inspect.Signature.empty:
            required.append(parameter.name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def _is_pydantic_model(value: Any) -> bool:
    return inspect.isclass(value) and issubclass(value, BaseModel)


def _schema_for_annotation(annotation: Any) -> dict[str, Any]:
    try:
        return TypeAdapter(annotation).json_schema()
    except Exception:
        origin = get_origin(annotation)
        args = get_args(annotation)
        if origin is list and args:
            return {"type": "array", "items": _schema_for_annotation(args[0])}
        return {"type": "string"}
