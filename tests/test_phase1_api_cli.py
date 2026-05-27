from __future__ import annotations

import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from prime_swarm_core.api import create_app
from prime_swarm_core.cli.main import app as cli_app
from prime_swarm_core.product import InMemoryRunStore, RunRecord, SQLiteRunStore


class TestPhase1Api(unittest.TestCase):
    def test_health_route_is_public(self) -> None:
        client = TestClient(create_app(InMemoryRunStore()))

        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_run_routes_require_api_key(self) -> None:
        client = TestClient(create_app(InMemoryRunStore()))

        response = client.post("/v1/runs", json={"question": "What is the heist rule?"})

        self.assertEqual(response.status_code, 401)

    def test_create_and_get_run(self) -> None:
        client = TestClient(create_app(InMemoryRunStore()))
        headers = {"x-api-key": "dev-key"}

        created = client.post(
            "/v1/runs",
            json={"question": "What is the heist rule?"},
            headers=headers,
        )
        payload = created.json()
        fetched = client.get(f"/v1/runs/{payload['run_id']}", headers=headers)

        self.assertEqual(created.status_code, 200)
        self.assertEqual(payload["status"], "completed")
        self.assertIn("Mock research answer", payload["result"]["answer"])
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.json()["run_id"], payload["run_id"])

    def test_env_api_key_overrides_dev_key(self) -> None:
        with patch.dict("os.environ", {"PRIME_SWARM_API_KEY": "secret"}, clear=False):
            client = TestClient(create_app(InMemoryRunStore()))
            bad = client.post("/v1/runs", json={"question": "x"}, headers={"x-api-key": "dev-key"})
            good = client.post("/v1/runs", json={"question": "x"}, headers={"x-api-key": "secret"})

        self.assertEqual(bad.status_code, 401)
        self.assertEqual(good.status_code, 200)

    def test_app_uses_sqlite_store_when_env_is_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "runs.sqlite"
            with patch.dict("os.environ", {"PRIME_SWARM_RUN_DB": str(db_path)}, clear=False):
                client = TestClient(create_app())
                created = client.post(
                    "/v1/runs",
                    json={"question": "What persists?"},
                    headers={"x-api-key": "dev-key"},
                )

            payload = created.json()
            restored = asyncio.run(SQLiteRunStore(db_path).get(payload["run_id"]))

        self.assertEqual(created.status_code, 200)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.question, "What persists?")


class TestPhase1Cli(unittest.TestCase):
    def test_cli_health(self) -> None:
        runner = CliRunner()

        result = runner.invoke(cli_app, ["health"])

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), "ok")

    def test_cli_research_json(self) -> None:
        runner = CliRunner()

        result = runner.invoke(cli_app, ["research", "What is the heist rule?", "--json"])
        payload = json.loads(result.stdout)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(payload["status"], "completed")
        self.assertIn("Mock research answer", payload["result"]["answer"])

    def test_cli_research_can_persist_to_sqlite(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "runs.sqlite"

            result = runner.invoke(cli_app, ["research", "Persist me", "--json", "--db", str(db_path)])
            payload = json.loads(result.stdout)
            restored = asyncio.run(SQLiteRunStore(db_path).get(payload["run_id"]))

        self.assertEqual(result.exit_code, 0)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.question, "Persist me")


class TestSQLiteRunStore(unittest.TestCase):
    def test_sqlite_run_store_survives_recreation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "runs.sqlite"
            record = RunRecord(
                run_id="run-1",
                question="What is durable?",
                status="completed",
                result={"answer": "SQLite", "confidence": 0.9},
            )

            asyncio.run(SQLiteRunStore(db_path).put(record))
            restored = asyncio.run(SQLiteRunStore(db_path).get("run-1"))

        self.assertIsNotNone(restored)
        self.assertEqual(restored.result, {"answer": "SQLite", "confidence": 0.9})
        self.assertEqual(restored.created_at, record.created_at)

    def test_sqlite_run_store_tracks_schema_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = SQLiteRunStore(Path(tmpdir) / "runs.sqlite")

            self.assertEqual(store.schema(), "1")


if __name__ == "__main__":
    unittest.main()
