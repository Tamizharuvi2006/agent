from __future__ import annotations

import unittest

from prime_swarm_core.debate import GroupChat
from prime_swarm_core.roles import DEVILS_ADVOCATE, SKEPTIC, Role
from prime_swarm_core.tracing import EvalExample, EvalResult, InMemorySpanExporter, evaluate_dataset, trace
from prime_swarm_core.workflows import WorkflowBuilder


class TestTracing(unittest.TestCase):
    def test_trace_exports_otel_shaped_span(self) -> None:
        exporter = InMemorySpanExporter()

        with trace("worker.run", inputs={"question": "why"}, exporter=exporter) as span:
            span.add_event("tool.call", tool="search")
            span.add_score("relevance", 0.9)
            span.outputs = {"answer": "because"}

        exported = exporter.spans[0]

        self.assertEqual(exported["name"], "worker.run")
        self.assertEqual(exported["attributes"]["inputs"]["question"], "why")
        self.assertEqual(exported["attributes"]["outputs"]["answer"], "because")
        self.assertEqual(exported["attributes"]["scores"]["relevance"], 0.9)
        self.assertEqual(exported["events"][0]["name"], "tool.call")

    def test_nested_trace_keeps_parent_context(self) -> None:
        child_exporter = InMemorySpanExporter()

        with trace("parent") as parent:
            with trace("child", exporter=child_exporter):
                pass

        child = child_exporter.spans[0]

        self.assertEqual(child["context"]["trace_id"], parent.trace_id)
        self.assertEqual(child["parent_span_id"], parent.span_id)

    def test_evaluate_dataset_calls_local_evaluator(self) -> None:
        examples = [EvalExample(id="1", inputs={"q": "x"}, expected_outputs={"answer": "yes"})]
        runs = {"1": {"answer": "yes"}}

        def evaluator(run: dict, example: EvalExample) -> EvalResult:
            score = 1.0 if run["answer"] == example.expected_outputs["answer"] else 0.0
            return EvalResult(example_id=example.id, scores={"accuracy": score})

        results = evaluate_dataset(runs, examples, evaluator)

        self.assertEqual(results[0].scores["accuracy"], 1.0)


class TestWorkflowBuilder(unittest.TestCase):
    def test_workflow_builder_creates_spec(self) -> None:
        spec = (
            WorkflowBuilder("research")
            .step("route", "route_activity")
            .then("plan", "plan_activity")
            .branch("review", condition="needs_human", branches={"true": "hitl", "false": "execute"})
            .parallel("execute", ["search", "debate"])
            .build()
        )

        self.assertEqual(spec.step_names(), ("route", "plan", "review", "execute"))
        self.assertEqual(spec.steps[0].next_step, "plan")
        self.assertEqual(spec.steps[2].branches["true"], "hitl")
        self.assertEqual(spec.as_dict()["steps"][3]["parallel_steps"], ["search", "debate"])

    def test_workflow_rejects_duplicate_steps(self) -> None:
        builder = WorkflowBuilder("bad").step("one", "activity")

        with self.assertRaises(ValueError):
            builder.step("one", "other")


class TestRoles(unittest.TestCase):
    def test_role_prompt_includes_sop(self) -> None:
        role = Role(
            name="reviewer",
            goal="Check the answer.",
            backstory="Careful and direct.",
            allowed_tools=("search",),
            expected_output="Findings.",
            sop=("Read claim.", "Check evidence."),
        )

        prompt = role.system_prompt()

        self.assertIn("Goal: Check the answer.", prompt)
        self.assertIn("Allowed tools: search", prompt)
        self.assertIn("1. Read claim.", prompt)

    def test_role_library_is_available(self) -> None:
        self.assertEqual(SKEPTIC.name, "skeptic")
        self.assertEqual(DEVILS_ADVOCATE.name, "devils_advocate")


class FakeSpeaker:
    def __init__(self, role: Role, responses: list[str]) -> None:
        self.role = role
        self.responses = responses

    async def respond(self, topic, transcript):
        return self.responses.pop(0)


class TestGroupChat(unittest.IsolatedAsyncioTestCase):
    async def test_group_chat_rotates_speakers_and_stops_on_consensus(self) -> None:
        skeptic = FakeSpeaker(SKEPTIC, ["risk noted"])
        advocate = FakeSpeaker(DEVILS_ADVOCATE, ["[consensus] acceptable with caveat"])
        chat = GroupChat(speakers=(skeptic, advocate), max_rounds=4)

        result = await chat.run("Should we ship?")

        self.assertEqual(len(result.transcript), 2)
        self.assertEqual(result.transcript[0].speaker, "skeptic")
        self.assertIn("acceptable", result.summary)


if __name__ == "__main__":
    unittest.main()

