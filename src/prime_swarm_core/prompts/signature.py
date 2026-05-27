"""DSPy-inspired typed prompt signatures."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, TypeAdapter


@dataclass(frozen=True, slots=True)
class FieldSpec:
    name: str
    type_: type
    description: str = ""
    required: bool = True

    def schema(self) -> dict[str, Any]:
        schema = TypeAdapter(self.type_).json_schema()
        if self.description:
            schema["description"] = self.description
        return schema


@dataclass(frozen=True, slots=True)
class Signature:
    """A typed contract for one LLM call."""

    name: str
    instruction: str
    input_fields: tuple[FieldSpec, ...]
    output_fields: tuple[FieldSpec, ...]
    examples: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    def render_prompt(self, **inputs: Any) -> str:
        missing = [spec.name for spec in self.input_fields if spec.required and spec.name not in inputs]
        if missing:
            raise ValueError(f"missing required inputs: {', '.join(missing)}")

        sections = [self.instruction.strip(), "", "Inputs:"]
        for spec in self.input_fields:
            value = inputs.get(spec.name)
            sections.append(f"- {spec.name}: {value}")

        if self.examples:
            sections.extend(["", "Examples:"])
            for index, example in enumerate(self.examples, start=1):
                sections.append(f"Example {index}:")
                sections.append(json.dumps(example, indent=2, sort_keys=True))

        sections.extend(
            [
                "",
                "Return JSON matching this schema:",
                json.dumps(self.output_schema(), indent=2, sort_keys=True),
            ]
        )
        return "\n".join(sections)

    def output_schema(self) -> dict[str, Any]:
        required = [spec.name for spec in self.output_fields if spec.required]
        return {
            "type": "object",
            "properties": {spec.name: spec.schema() for spec in self.output_fields},
            "required": required,
            "additionalProperties": False,
        }

    def parse_output(self, raw: str | dict[str, Any]) -> dict[str, Any]:
        data = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(data, dict):
            raise TypeError("signature output must be a JSON object")

        parsed: dict[str, Any] = {}
        for spec in self.output_fields:
            if spec.name not in data:
                if spec.required:
                    raise ValueError(f"missing required output field: {spec.name}")
                continue
            parsed[spec.name] = TypeAdapter(spec.type_).validate_python(data[spec.name])
        return parsed

    def with_examples(self, examples: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> "Signature":
        return Signature(
            name=self.name,
            instruction=self.instruction,
            input_fields=self.input_fields,
            output_fields=self.output_fields,
            examples=tuple(examples),
        )

