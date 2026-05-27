"""Few-shot bootstrapping for prompt signatures."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from prime_swarm_core.prompts.signature import Signature
from prime_swarm_core.tracing.evals import EvalExample


ExampleRunner = Callable[[Signature, EvalExample], Awaitable[dict[str, Any]]]
ExampleScorer = Callable[[dict[str, Any], EvalExample], float]


async def bootstrap_few_shot(
    signature: Signature,
    train_set: list[EvalExample],
    runner: ExampleRunner,
    scorer: ExampleScorer,
    *,
    k: int = 4,
    threshold: float = 0.8,
) -> Signature:
    if k <= 0:
        raise ValueError("k must be positive")
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")

    examples: list[dict[str, Any]] = []
    for example in train_set:
        output = await runner(signature, example)
        score = scorer(output, example)
        if score >= threshold:
            examples.append(
                {
                    "inputs": example.inputs,
                    "outputs": output,
                    "score": score,
                }
            )
        if len(examples) >= k:
            break
    return signature.with_examples(examples)

