from __future__ import annotations

import asyncio
import os
import unittest

from prime_swarm_core.product import HTTPJSONSearchProvider, InMemoryRunStore, run_research


def _live_search_enabled() -> bool:
    return os.getenv("RUN_LIVE_SEARCH_TESTS") == "1" and bool(os.getenv("PRIME_SWARM_SEARCH_URL"))


@unittest.skipUnless(_live_search_enabled(), "set RUN_LIVE_SEARCH_TESTS=1 and PRIME_SWARM_SEARCH_URL")
class TestLiveSearchSmoke(unittest.TestCase):
    def test_live_search_provider_and_research_flow(self) -> None:
        provider = HTTPJSONSearchProvider(
            os.environ["PRIME_SWARM_SEARCH_URL"],
            api_key=os.getenv("PRIME_SWARM_SEARCH_API_KEY"),
        )

        results = asyncio.run(provider.search("agent runtime checkpointing", k=3))
        self.assertGreater(len(results), 0)
        self.assertTrue(results[0].url)
        self.assertTrue(results[0].title)

        record = asyncio.run(
            run_research(
                "What is agent runtime checkpointing?",
                InMemoryRunStore(),
                search_provider=provider,
                use_web_search=True,
                top_k=3,
            )
        )

        self.assertEqual(record.status, "completed")
        self.assertIn("sources", record.result)
        self.assertGreater(len(record.result["sources"]), 0)


if __name__ == "__main__":
    unittest.main()
