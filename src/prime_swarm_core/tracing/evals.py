"""Eval dataset and evaluator helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class EvalExample:
    id: str
    inputs: dict[str, Any]
    expected_outputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EvalResult:
    example_id: str
    scores: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)


Evaluator = Callable[[dict[str, Any], EvalExample], EvalResult]


def evaluate_dataset(
    runs: dict[str, dict[str, Any]],
    examples: list[EvalExample],
    evaluator: Evaluator,
) -> list[EvalResult]:
    results: list[EvalResult] = []
    for example in examples:
        if example.id not in runs:
            raise KeyError(f"missing run for example {example.id}")
        results.append(evaluator(runs[example.id], example))
    return results

