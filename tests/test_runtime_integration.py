from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from prime_swarm_core.determinism import DeterminismContext
from prime_swarm_core.graph import Command, GraphLimitExceeded, GraphRunner, SQLiteCheckpointer, Send
from prime_swarm_core.llm import BudgetTracker, MockChatModel, OpenAICompatibleChatModel, StructuredCallFailed, call_signature
from prime_swarm_core.prompts import FieldSpec, Signature
from prime_swarm_core.tracing import InMemorySpanExporter, JSONLSpanExporter, MultiSpanExporter
from prime_swarm_core.tracing.viewer import render_trace_tree


class TestRuntimeIntegration(unittest.IsolatedAsyncioTestCase):
    async def test_graph_runner_persists_checkpoints_and_exports_spans(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            db_path = root / "checkpoints.sqlite3"
            trace_path = root / "spans.jsonl"

            async def first(state):
                return Command.to("second", seen=state.values["seed"] + 1)

            def second(state):
                return Command.to(None, final=state.values["seen"] + 1)

            checkpointer = SQLiteCheckpointer(db_path)
            runner = GraphRunner(
                {"first": first, "second": second},
                checkpointer=checkpointer,
                trace_exporter=JSONLSpanExporter(trace_path),
            )

            result = await runner.run("run-1", start_at="first", initial_values={"seed": 1})
            history = await checkpointer.list("run-1")
            restarted = SQLiteCheckpointer(db_path)
            latest_after_restart = await restarted.get("run-1")
            trace_lines = trace_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(result.state.status, "done")
        self.assertEqual(result.state.values["final"], 3)
        self.assertGreaterEqual(len(history), 3)
        self.assertEqual(latest_after_restart.values["final"], 3)
        self.assertEqual(len(trace_lines), 2)
        self.assertEqual(json.loads(trace_lines[0])["name"], "graph.node")

    async def test_sqlite_checkpointer_delete_and_schema_version(self) -> None:
        with TemporaryDirectory() as temp_dir:
            checkpointer = SQLiteCheckpointer(Path(temp_dir) / "checkpoints.sqlite3")
            await checkpointer.put("run-1", await _state("run-1", value=1))
            await checkpointer.put("run-1", await _state("run-1", value=2))

            self.assertEqual(checkpointer.get_schema_version(), 1)
            self.assertEqual((await checkpointer.get("run-1")).values["value"], 2)

            await checkpointer.delete("run-1")
            latest = await checkpointer.get("run-1")

        self.assertIsNone(latest)

    async def test_graph_runner_supports_command_interrupt(self) -> None:
        async def needs_human(state):
            return Command.pause({"question": "approve?"})

        runner = GraphRunner({"needs_human": needs_human})

        result = await runner.run("run-2", start_at="needs_human")

        self.assertTrue(result.interrupted)
        self.assertEqual(result.interrupt_payload["question"], "approve?")
        self.assertEqual(result.state.status, "interrupted")

    async def test_graph_runner_resumes_without_reexecuting_completed_steps(self) -> None:
        calls = {"first": 0, "second": 0, "third": 0}

        def first(state):
            calls["first"] += 1
            return Command.to("second", one=True)

        def second(state):
            calls["second"] += 1
            return Command.to("third", two=True)

        def third(state):
            calls["third"] += 1
            return Command.to(None, three=True)

        with TemporaryDirectory() as temp_dir:
            checkpointer = SQLiteCheckpointer(Path(temp_dir) / "checkpoints.sqlite3")
            runner = GraphRunner(
                {"first": first, "second": second, "third": third},
                checkpointer=checkpointer,
                max_steps=2,
            )
            with self.assertRaises(GraphLimitExceeded):
                await runner.run("resume-run", start_at="first")

            resumed = GraphRunner(
                {"first": first, "second": second, "third": third},
                checkpointer=SQLiteCheckpointer(Path(temp_dir) / "checkpoints.sqlite3"),
            )
            result = await resumed.run("resume-run", start_at="first")

        self.assertEqual(result.state.status, "done")
        self.assertEqual(calls, {"first": 1, "second": 1, "third": 1})

    async def test_graph_runner_fanout_and_limits(self) -> None:
        def root(state):
            return Command.fanout(
                [Send("left", {"side": "left"}), Send("right", {"side": "right"})],
                root=True,
            )

        def left(state):
            return Command.stay(answer=f"{state.values['side']}-done")

        def right(state):
            return Command.stay(answer=f"{state.values['side']}-done")

        runner = GraphRunner({"root": root, "left": left, "right": right})
        result = await runner.run("fanout-run", start_at="root")

        self.assertEqual(result.state.values["fanout"][0]["update"]["answer"], "left-done")
        self.assertEqual(result.state.values["fanout"][1]["update"]["answer"], "right-done")

        loop_runner = GraphRunner({"loop": lambda state: Command.to("loop")}, max_steps=1)
        with self.assertRaises(GraphLimitExceeded):
            await loop_runner.run("loop-run", start_at="loop")

    async def test_openai_compatible_model_and_signature_adapter(self) -> None:
        captured = {}
        budget = BudgetTracker()

        async def fake_transport(url, headers, payload):
            captured["url"] = url
            captured["payload"] = payload
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"answer": "Steal patterns, not packages.", "confidence": 0.95}'
                        }
                    }
                ],
                "usage": {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12},
            }

        model = OpenAICompatibleChatModel(
            model="test-model",
            api_key="test-key",
            base_url="https://example.test/v1",
            transport=fake_transport,
            budget_tracker=budget,
        )
        signature = Signature(
            name="answer",
            instruction="Answer the question.",
            input_fields=(FieldSpec("question", str),),
            output_fields=(FieldSpec("answer", str), FieldSpec("confidence", float),),
        )

        output = await call_signature(model, signature, question="Rule?")

        self.assertEqual(output["answer"], "Steal patterns, not packages.")
        self.assertEqual(output["confidence"], 0.95)
        self.assertEqual(captured["url"], "https://example.test/v1/chat/completions")
        self.assertEqual(captured["payload"]["response_format"], {"type": "json_object"})
        self.assertEqual(budget.total_tokens, 12)

    async def test_mock_model_retries_and_failure_path(self) -> None:
        signature = Signature(
            name="answer",
            instruction="Answer the question.",
            input_fields=(FieldSpec("question", str),),
            output_fields=(FieldSpec("answer", str), FieldSpec("confidence", float),),
        )
        model = MockChatModel([
            '{"answer": "bad", "confidence": "not-float"}',
            {"answer": "ok", "confidence": 0.8},
        ])

        output = await call_signature(model, signature, question="Rule?")

        self.assertEqual(output["confidence"], 0.8)
        self.assertEqual(len(model.calls), 2)

        failing = MockChatModel(['{"answer": "bad", "confidence": "no"}'])
        with self.assertRaises(StructuredCallFailed):
            await call_signature(failing, signature, question="Rule?", max_retries=1)

    async def test_multi_exporter_and_trace_viewer(self) -> None:
        memory_exporter = InMemorySpanExporter()
        with TemporaryDirectory() as temp_dir:
            trace_path = Path(temp_dir) / "trace.jsonl"
            multi = MultiSpanExporter([memory_exporter, JSONLSpanExporter(trace_path)])
            runner = GraphRunner({"one": lambda state: Command.to(None, done=True)}, trace_exporter=multi)

            await runner.run("trace-run", start_at="one")
            rendered = render_trace_tree(trace_path)

        self.assertEqual(len(memory_exporter.spans), 1)
        self.assertIn("graph.node", rendered)
        self.assertIn("done", rendered)

    def test_determinism_context_replays_identically(self) -> None:
        first = DeterminismContext(seed=7)
        second = DeterminismContext(seed=7)

        first_values = [first.now().isoformat(), str(first.uuid4()), first.random()]
        second_values = [second.now().isoformat(), str(second.uuid4()), second.random()]

        self.assertEqual(first_values, second_values)


async def _state(run_id: str, value: int):
    from prime_swarm_core.graph import RunState

    return RunState(run_id=run_id, values={"value": value})


if __name__ == "__main__":
    unittest.main()
