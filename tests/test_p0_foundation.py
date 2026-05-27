from __future__ import annotations

import unittest
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import BaseModel, Field

from prime_swarm_core.data import Document, load_csv, load_directory, load_file, load_json, load_text, markdown_split, recursive_split
from prime_swarm_core.graph import Command, HumanInterrupt, InMemoryCheckpointer, RunState, Send, interrupt
from prime_swarm_core.llm import StructuredCallFailed, call_structured
from prime_swarm_core.quality import SearchResult, rerank_sources
from prime_swarm_core.tools import ToolRegistry, tool


class TestGraphPrimitives(unittest.IsolatedAsyncioTestCase):
    async def test_command_and_checkpointer(self) -> None:
        command = Command.fanout([Send("worker", {"q": "x"})], answer="draft")

        self.assertEqual(command.update["answer"], "draft")
        self.assertEqual(command.send[0].target, "worker")

        checkpointer = InMemoryCheckpointer()
        state = RunState(run_id="run-1").with_update(answer="draft")
        await checkpointer.put("run-1", state)
        await checkpointer.put("run-1", state.with_status("done"))

        latest = await checkpointer.get("run-1")
        history = await checkpointer.list("run-1")

        self.assertEqual(latest.status, "done")
        self.assertEqual(len(history), 2)

    async def test_interrupt_payload(self) -> None:
        with self.assertRaises(HumanInterrupt) as raised:
            interrupt({"reason": "approval required"})

        self.assertEqual(raised.exception.payload["reason"], "approval required")


class TestDataPrimitives(unittest.TestCase):
    def test_recursive_split_preserves_metadata(self) -> None:
        doc = Document("alpha beta gamma delta epsilon", {"source": "unit"})
        chunks = recursive_split(doc, chunk_size=12, overlap=2)

        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0].metadata["source"], "unit")
        self.assertEqual(chunks[0].metadata["chunk_index"], 0)

    def test_markdown_split_by_heading(self) -> None:
        doc = Document("# One\nBody\n## Two\nMore")
        chunks = markdown_split(doc)

        self.assertEqual([chunk.metadata["heading"] for chunk in chunks], ["One", "Two"])

    def test_local_loaders_create_documents_with_metadata(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            text_path = root / "note.md"
            json_path = root / "data.json"
            csv_path = root / "rows.csv"

            text_path.write_text("# Note\nHello", encoding="utf-8")
            json_path.write_text('{"name": "core", "ok": true}', encoding="utf-8")
            csv_path.write_text("name,score\nalpha,1\nbeta,2\n", encoding="utf-8")

            text_docs = load_text(text_path)
            json_docs = load_json(json_path)
            csv_docs = load_csv(csv_path)
            auto_json_docs = load_file(json_path)
            directory_docs = load_directory(root)

        self.assertEqual(text_docs[0].metadata["loader"], "text")
        self.assertEqual(json_docs[0].metadata["json_type"], "dict")
        self.assertEqual(len(csv_docs), 2)
        self.assertEqual(csv_docs[1].metadata["row_index"], 1)
        self.assertEqual(auto_json_docs[0].metadata["loader"], "json")
        self.assertEqual(len(directory_docs), 4)


class SearchArgs(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=10)


class TestTools(unittest.TestCase):
    def test_tool_registry_supports_pydantic_arg_model(self) -> None:
        registry = ToolRegistry()

        @tool("search", allowed_in=["research"], registry=registry)
        async def search(args: SearchArgs) -> str:
            """Search test corpus."""
            return args.query

        definition = registry.get("search")

        self.assertEqual(definition.name, "search")
        self.assertEqual(definition.allowed_in, ("research",))
        self.assertIn("query", definition.schema["properties"])

    def test_tool_registry_builds_schema_from_plain_signature(self) -> None:
        registry = ToolRegistry()

        @tool(registry=registry)
        def add(left: int, right: int = 1) -> int:
            return left + right

        schema = registry.get("add").schema

        self.assertEqual(schema["required"], ["left"])
        self.assertEqual(schema["properties"]["left"]["type"], "integer")


class Answer(BaseModel):
    answer: str
    confidence: float = Field(ge=0, le=1)


class TestStructuredCalls(unittest.IsolatedAsyncioTestCase):
    async def test_retries_until_validation_succeeds(self) -> None:
        responses = iter([
            '{"answer": "ok", "confidence": 2}',
            '{"answer": "ok", "confidence": 0.8}',
        ])

        async def fake_call(messages):
            return next(responses)

        result = await call_structured(fake_call, "answer", Answer)

        self.assertEqual(result.answer, "ok")
        self.assertEqual(result.confidence, 0.8)

    async def test_raises_after_retry_budget(self) -> None:
        async def fake_call(messages):
            return '{"answer": "bad", "confidence": 2}'

        with self.assertRaises(StructuredCallFailed):
            await call_structured(fake_call, "answer", Answer, max_retries=1)


class TestSourceRanker(unittest.TestCase):
    def test_reranks_quality_and_freshness(self) -> None:
        today = date(2026, 5, 27)
        results = [
            SearchResult(
                url="https://example.medium.com/post",
                title="Blog",
                score=0.8,
                published_date=today,
            ),
            SearchResult(
                url="https://docs.vendor.com/guide",
                title="Official docs",
                score=0.7,
                published_date=today - timedelta(days=5),
            ),
            SearchResult(
                url="https://agency.gov/report",
                title="Official report",
                score=0.65,
                published_date=today - timedelta(days=5),
            ),
        ]

        ranked = rerank_sources(results, needs_freshness=True, today=today)

        self.assertEqual(ranked[0].url, "https://agency.gov/report")
        self.assertGreater(ranked[0].score, ranked[-1].score)


if __name__ == "__main__":
    unittest.main()
