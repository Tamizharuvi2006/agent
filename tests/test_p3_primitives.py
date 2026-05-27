from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from prime_swarm_core.agents import Agent
from prime_swarm_core.code_actions import CodeActionPolicy, review_code_action
from prime_swarm_core.data import Document
from prime_swarm_core.diffs import make_unified_diff
from prime_swarm_core.handoff import handoff
from prime_swarm_core.plugins import discover_plugins, load_plugin
from prime_swarm_core.retrievers import InMemoryKeywordRetriever
from prime_swarm_core.roles import SKEPTIC
from prime_swarm_core.sops import SOPTemplate, render_sop
from prime_swarm_core.tools import ToolRegistry, tool


class TestHandoff(unittest.TestCase):
    def test_handoff_requires_reason(self) -> None:
        result = handoff("quant", context={"rows": 10}, reason="needs numerical analysis")

        self.assertEqual(result.target_agent, "quant")
        self.assertEqual(result.context["rows"], 10)

        with self.assertRaises(ValueError):
            handoff("quant")


class MemoryStub:
    async def recall(self, query: str, k: int = 5) -> list[str]:
        return [f"remembered {query}"]


class TestComposableAgent(unittest.IsolatedAsyncioTestCase):
    async def test_agent_prepares_context_messages(self) -> None:
        registry = ToolRegistry()

        @tool(registry=registry)
        def lookup(query: str) -> str:
            return query

        knowledge = InMemoryKeywordRetriever([Document("alpha strategy", {"source": "doc-1"})])
        agent = Agent(
            role=SKEPTIC,
            memory=MemoryStub(),
            knowledge=knowledge,
            tools=tuple(registry.list()),
        )

        messages = await agent.prepare_messages("alpha")
        content = "\n".join(message["content"] for message in messages)

        self.assertEqual(messages[-1]["role"], "user")
        self.assertIn("Relevant memory", content)
        self.assertIn("Knowledge hits", content)
        self.assertIn("Available tools: lookup", content)


class TestPlugins(unittest.TestCase):
    def test_discovers_plugin_folder(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plugin = root / "web_search"
            examples = plugin / "examples"
            examples.mkdir(parents=True)
            (plugin / "schema.json").write_text('{"name": "web_search", "description": "Search"}', encoding="utf-8")
            (plugin / "README.md").write_text("# Web Search", encoding="utf-8")
            (examples / "basic.json").write_text('{"query": "x"}', encoding="utf-8")

            loaded = load_plugin(plugin)
            discovered = discover_plugins(root)

        self.assertEqual(loaded.name, "web_search")
        self.assertIn("Web Search", loaded.readme)
        self.assertEqual(len(loaded.examples), 1)
        self.assertEqual(discovered[0].name, "web_search")


class TestSOPs(unittest.TestCase):
    def test_sop_template_renders_steps_and_output(self) -> None:
        template = SOPTemplate(
            name="research",
            steps=("Identify entities.", "Check sources."),
            output_template="Claims:\n- ...",
        )

        rendered = template.render()

        self.assertIn("1. Identify entities.", rendered)
        self.assertIn("Claims:", rendered)

    def test_render_sop_rejects_empty_steps(self) -> None:
        with self.assertRaises(ValueError):
            render_sop([], "Output")


class TestCodeActions(unittest.TestCase):
    def test_code_action_disabled_by_default(self) -> None:
        review = review_code_action("result = 1 + 1")

        self.assertFalse(review.allowed)
        self.assertIn("code-as-action is disabled", review.reasons)

    def test_code_action_blocks_unsafe_import_even_when_enabled(self) -> None:
        review = review_code_action("import os\nresult = os.getcwd()", CodeActionPolicy(enabled=True))

        self.assertFalse(review.allowed)
        self.assertIn("blocked import: os", review.reasons)

    def test_code_action_allows_simple_expression_when_enabled(self) -> None:
        review = review_code_action("result = sum([1, 2, 3])", CodeActionPolicy(enabled=True))

        self.assertTrue(review.allowed)


class TestDiffs(unittest.TestCase):
    def test_make_unified_diff(self) -> None:
        diff = make_unified_diff("a\nb\n", "a\nc\n", fromfile="old.md", tofile="new.md")

        self.assertIn("--- old.md", diff)
        self.assertIn("+++ new.md", diff)
        self.assertIn("-b", diff)
        self.assertIn("+c", diff)


if __name__ == "__main__":
    unittest.main()

