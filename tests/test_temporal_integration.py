from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from prime_swarm_core.graph import Command, GraphRunner, SQLiteCheckpointer
from prime_swarm_core.workflows import (
    TemporalGraphRequest,
    clear_temporal_graphs,
    create_temporal_worker,
    register_temporal_graph,
    run_local_graph_activity,
)


class TestTemporalIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self) -> None:
        clear_temporal_graphs()

    async def test_temporal_activity_matches_local_graph_runner(self) -> None:
        def first(state):
            return Command.to("second", one=state.values["seed"] + 1)

        def second(state):
            return Command.to(None, final=state.values["one"] + 1)

        nodes = {"first": first, "second": second}

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            local_runner = GraphRunner(
                nodes,
                checkpointer=SQLiteCheckpointer(root / "local.sqlite3"),
            )
            local = await local_runner.run("local-run", start_at="first", initial_values={"seed": 1})

            register_temporal_graph("demo", nodes)
            temporal = await run_local_graph_activity(
                TemporalGraphRequest(
                    graph_name="demo",
                    run_id="temporal-run",
                    start_at="first",
                    initial_values={"seed": 1},
                    sqlite_path=str(root / "temporal.sqlite3"),
                    trace_path=str(root / "temporal.jsonl"),
                )
            )

        self.assertEqual(temporal.status, local.state.status)
        self.assertEqual(temporal.values, local.state.values)
        self.assertEqual(temporal.steps, local.steps)

    async def test_temporal_activity_rejects_unknown_graph(self) -> None:
        with self.assertRaises(KeyError):
            await run_local_graph_activity(
                TemporalGraphRequest(graph_name="missing", run_id="run", start_at="start")
            )

    def test_worker_factory_uses_temporal_worker_type(self) -> None:
        self.assertTrue(callable(create_temporal_worker))


if __name__ == "__main__":
    unittest.main()

