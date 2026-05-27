"""LLM budget accounting."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BudgetRecord:
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float = 0.0


class BudgetTracker:
    def __init__(self) -> None:
        self.records: list[BudgetRecord] = []

    def record(
        self,
        *,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int | None = None,
        cost: float = 0.0,
    ) -> None:
        total = total_tokens if total_tokens is not None else prompt_tokens + completion_tokens
        self.records.append(
            BudgetRecord(
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total,
                cost=cost,
            )
        )

    @property
    def total_tokens(self) -> int:
        return sum(record.total_tokens for record in self.records)

    @property
    def total_cost(self) -> float:
        return sum(record.cost for record in self.records)

