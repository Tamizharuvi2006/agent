"""Small eval-driven prompt optimizer.

This is inspired by DSPy optimizer patterns but keeps the runtime local and
explicit: callers provide candidates, runner, and scorer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from prime_swarm_core.prompts.signature import Signature
from prime_swarm_core.tracing.evals import EvalExample


PromptRunner = Callable[[Signature, EvalExample], Awaitable[dict]]
PromptScorer = Callable[[dict, EvalExample], float]


@dataclass(frozen=True, slots=True)
class PromptCandidate:
    instruction: str
    score: float


async def optimize_prompt(
    signature: Signature,
    eval_set: list[EvalExample],
    candidate_instructions: list[str],
    runner: PromptRunner,
    scorer: PromptScorer,
) -> PromptCandidate:
    if not candidate_instructions:
        raise ValueError("candidate_instructions cannot be empty")
    if not eval_set:
        raise ValueError("eval_set cannot be empty")

    best: PromptCandidate | None = None
    for instruction in candidate_instructions:
        candidate = Signature(
            name=signature.name,
            instruction=instruction,
            input_fields=signature.input_fields,
            output_fields=signature.output_fields,
            examples=signature.examples,
        )
        scores = []
        for example in eval_set:
            output = await runner(candidate, example)
            scores.append(scorer(output, example))
        average = sum(scores) / len(scores)
        current = PromptCandidate(instruction=instruction, score=average)
        if best is None or current.score > best.score:
            best = current
    return best

