from __future__ import annotations

import unittest

from prime_swarm_core.data import Document
from prime_swarm_core.optimizers import bootstrap_few_shot, optimize_prompt
from prime_swarm_core.prompts import FieldSpec, Signature
from prime_swarm_core.retrievers import AutoMergingRetriever, InMemoryKeywordRetriever
from prime_swarm_core.tracing import EvalExample


def make_signature(instruction: str = "Answer carefully.") -> Signature:
    return Signature(
        name="answer",
        instruction=instruction,
        input_fields=(FieldSpec("question", str, "User question"),),
        output_fields=(
            FieldSpec("answer", str, "Answer text"),
            FieldSpec("confidence", float, "0 to 1 confidence"),
        ),
    )


class TestSignatures(unittest.TestCase):
    def test_signature_renders_schema_and_parses_output(self) -> None:
        signature = make_signature()

        prompt = signature.render_prompt(question="Why?")
        parsed = signature.parse_output('{"answer": "Because", "confidence": 0.7}')

        self.assertIn("Answer carefully.", prompt)
        self.assertIn("question", prompt)
        self.assertEqual(parsed["answer"], "Because")
        self.assertEqual(parsed["confidence"], 0.7)

    def test_signature_rejects_missing_required_input(self) -> None:
        signature = make_signature()

        with self.assertRaises(ValueError):
            signature.render_prompt()


class TestOptimizers(unittest.IsolatedAsyncioTestCase):
    async def test_bootstrap_few_shot_keeps_high_scoring_examples(self) -> None:
        signature = make_signature()
        train_set = [
            EvalExample(id="1", inputs={"question": "A"}, expected_outputs={"answer": "yes"}),
            EvalExample(id="2", inputs={"question": "B"}, expected_outputs={"answer": "no"}),
        ]

        async def runner(current_signature: Signature, example: EvalExample) -> dict:
            return {"answer": example.expected_outputs["answer"], "confidence": 0.9}

        def scorer(output: dict, example: EvalExample) -> float:
            return 1.0 if output["answer"] == example.expected_outputs["answer"] else 0.0

        optimized = await bootstrap_few_shot(signature, train_set, runner, scorer, k=1)

        self.assertEqual(len(optimized.examples), 1)
        self.assertEqual(optimized.examples[0]["score"], 1.0)

    async def test_optimize_prompt_selects_best_candidate(self) -> None:
        signature = make_signature()
        eval_set = [EvalExample(id="1", inputs={"question": "Ship?"}, expected_outputs={"answer": "careful"})]

        async def runner(current_signature: Signature, example: EvalExample) -> dict:
            if "careful" in current_signature.instruction:
                return {"answer": "careful", "confidence": 0.9}
            return {"answer": "fast", "confidence": 0.5}

        def scorer(output: dict, example: EvalExample) -> float:
            return 1.0 if output["answer"] == example.expected_outputs["answer"] else 0.0

        winner = await optimize_prompt(
            signature,
            eval_set,
            ["Answer fast.", "Answer careful."],
            runner,
            scorer,
        )

        self.assertEqual(winner.instruction, "Answer careful.")
        self.assertEqual(winner.score, 1.0)


class TestAutoMergingRetriever(unittest.IsolatedAsyncioTestCase):
    async def test_keyword_retriever_returns_matching_documents(self) -> None:
        retriever = InMemoryKeywordRetriever(
            [
                Document("alpha planning notes"),
                Document("beta release notes"),
            ]
        )

        hits = await retriever.retrieve("alpha", k=1)

        self.assertEqual(hits[0].page_content, "alpha planning notes")

    async def test_auto_merging_returns_parent_when_sibling_threshold_met(self) -> None:
        parent = Document("Parent document about alpha strategy.", {"doc_id": "parent-1"})
        children = [
            Document("alpha detail one", {"parent_id": "parent-1", "chunk": 1}),
            Document("alpha detail two", {"parent_id": "parent-1", "chunk": 2}),
            Document("other alpha", {"parent_id": "parent-2", "chunk": 1}),
        ]
        child_retriever = InMemoryKeywordRetriever(children)
        retriever = AutoMergingRetriever(
            child_retriever,
            {"parent-1": parent},
            parent_threshold=2,
        )

        hits = await retriever.retrieve("alpha", k=3)

        self.assertEqual(hits[0].page_content, parent.page_content)
        self.assertEqual(hits[0].metadata["merged_from_children"], 2)
        self.assertEqual(hits[1].metadata["parent_id"], "parent-2")


if __name__ == "__main__":
    unittest.main()

