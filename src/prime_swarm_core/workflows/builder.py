"""Small fluent workflow specification builder.

This does not execute workflows and does not wrap Temporal yet. It only creates
a typed plan that later workflow integrations can consume.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    name: str
    kind: str
    target: str | None = None
    next_step: str | None = None
    condition: str | None = None
    branches: dict[str, str] = field(default_factory=dict)
    parallel_steps: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorkflowSpec:
    name: str
    steps: tuple[WorkflowStep, ...]

    def step_names(self) -> tuple[str, ...]:
        return tuple(step.name for step in self.steps)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "steps": [
                {
                    "name": step.name,
                    "kind": step.kind,
                    "target": step.target,
                    "next_step": step.next_step,
                    "condition": step.condition,
                    "branches": step.branches,
                    "parallel_steps": list(step.parallel_steps),
                    "metadata": step.metadata,
                }
                for step in self.steps
            ],
        }


class WorkflowBuilder:
    def __init__(self, name: str) -> None:
        self.name = name
        self._steps: list[WorkflowStep] = []
        self._names: set[str] = set()

    def step(self, name: str, target: str, **metadata: Any) -> "WorkflowBuilder":
        self._add(WorkflowStep(name=name, kind="step", target=target, metadata=metadata))
        return self

    def then(self, name: str, target: str, **metadata: Any) -> "WorkflowBuilder":
        if self._steps:
            previous = self._steps[-1]
            self._steps[-1] = WorkflowStep(
                name=previous.name,
                kind=previous.kind,
                target=previous.target,
                next_step=name,
                condition=previous.condition,
                branches=previous.branches,
                parallel_steps=previous.parallel_steps,
                metadata=previous.metadata,
            )
        return self.step(name, target, **metadata)

    def branch(
        self,
        name: str,
        *,
        condition: str,
        branches: dict[str, str],
        **metadata: Any,
    ) -> "WorkflowBuilder":
        if not branches:
            raise ValueError("branches cannot be empty")
        self._add(
            WorkflowStep(
                name=name,
                kind="branch",
                condition=condition,
                branches=dict(branches),
                metadata=metadata,
            )
        )
        return self

    def parallel(self, name: str, steps: list[str] | tuple[str, ...], **metadata: Any) -> "WorkflowBuilder":
        if len(steps) < 2:
            raise ValueError("parallel requires at least two steps")
        self._add(
            WorkflowStep(
                name=name,
                kind="parallel",
                parallel_steps=tuple(steps),
                metadata=metadata,
            )
        )
        return self

    def build(self) -> WorkflowSpec:
        if not self._steps:
            raise ValueError("workflow needs at least one step")
        return WorkflowSpec(name=self.name, steps=tuple(self._steps))

    def _add(self, step: WorkflowStep) -> None:
        if step.name in self._names:
            raise ValueError(f"duplicate workflow step: {step.name}")
        self._names.add(step.name)
        self._steps.append(step)

