from __future__ import annotations

import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
import httpx
from typer.testing import CliRunner

from prime_swarm_core.api import create_app
from prime_swarm_core.cli.http_client import CliHttpError, PrimeSwarmHttpClient
from prime_swarm_core.cli.main import app as cli_app
from prime_swarm_core.product import (
    HTTPJSONSearchProvider,
    InMemoryRunStore,
    RunRecord,
    SQLiteRunStore,
    StaticSearchProvider,
    run_research,
)
from prime_swarm_core.quality import SearchResult


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

    def test_create_run_can_use_local_source_path(self) -> None:
        client = TestClient(create_app(InMemoryRunStore()))
        headers = {"x-api-key": "dev-key"}
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "notes.md"
            source.write_text("# Heist Rule\nSteal patterns, not packages.", encoding="utf-8")

            response = client.post(
                "/v1/runs",
                json={"question": "What should we steal?", "source_path": str(source)},
                headers=headers,
            )
            payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("Steal patterns", payload["result"]["evidence"])
        self.assertEqual(payload["result"]["sources"][0]["title"], "Heist Rule")

    def test_create_run_can_use_web_search_provider(self) -> None:
        provider = StaticSearchProvider(
            [
                SearchResult(
                    url="https://docs.example.com/runtime",
                    title="Runtime docs",
                    snippet="External web search can feed the research graph.",
                    score=0.5,
                )
            ]
        )
        client = TestClient(create_app(InMemoryRunStore(), search_provider=provider))

        response = client.post(
            "/v1/runs",
            json={"question": "What feeds the graph?", "use_web_search": True},
            headers={"x-api-key": "dev-key"},
        )
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "completed")
        self.assertIn("External web search", payload["result"]["evidence"])
        self.assertEqual(payload["result"]["sources"][0]["source"], "https://docs.example.com/runtime")

    def test_web_search_without_provider_is_reported_honestly(self) -> None:
        client = TestClient(create_app(InMemoryRunStore()))

        response = client.post(
            "/v1/runs",
            json={"question": "What is current?", "use_web_search": True},
            headers={"x-api-key": "dev-key"},
        )
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["status"], "failed")
        self.assertIn("no search provider", payload["error"])


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

    def test_cli_research_can_use_local_source(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "research.md"
            source.write_text("# Runtime\nSQLite stores run records durably.", encoding="utf-8")

            result = runner.invoke(cli_app, ["research", "What stores records?", "--source", str(source), "--json"])
            payload = json.loads(result.stdout)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("SQLite stores run records", payload["result"]["evidence"])
        self.assertEqual(payload["result"]["sources"][0]["title"], "Runtime")

    def test_cli_health_can_call_http_api(self) -> None:
        runner = CliRunner()

        with patch("prime_swarm_core.cli.main.PrimeSwarmHttpClient") as client_type:
            client_type.return_value.health.return_value = {"status": "ok"}
            result = runner.invoke(cli_app, ["health", "--api-url", "http://api.test"])

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), "ok")
        client_type.assert_called_once_with("http://api.test")

    def test_cli_research_can_call_http_api(self) -> None:
        runner = CliRunner()
        api_payload = {
            "run_id": "run-http",
            "question": "Remote question",
            "status": "completed",
            "result": {"answer": "Remote answer"},
            "error": None,
            "created_at": "2026-05-27T00:00:00+00:00",
            "updated_at": "2026-05-27T00:00:00+00:00",
        }

        with patch("prime_swarm_core.cli.main.PrimeSwarmHttpClient") as client_type:
            client_type.return_value.create_run.return_value = api_payload
            result = runner.invoke(
                cli_app,
                [
                    "research",
                    "Remote question",
                    "--api-url",
                    "http://api.test",
                    "--api-key",
                    "secret",
                    "--source",
                    "docs",
                    "--top-k",
                    "3",
                    "--web",
                    "--json",
                ],
            )
            payload = json.loads(result.stdout)

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(payload["run_id"], "run-http")
        client_type.assert_called_once_with("http://api.test", api_key="secret")
        client_type.return_value.create_run.assert_called_once_with(
            "Remote question",
            source_path="docs",
            use_web_search=True,
            top_k=3,
        )


class TestCliHttpClient(unittest.TestCase):
    def test_http_client_creates_run_with_api_key(self) -> None:
        seen: dict[str, str] = {}
        body: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["path"] = request.url.path
            seen["api_key"] = request.headers["x-api-key"]
            body.update(json.loads(request.content))
            return httpx.Response(
                200,
                json={
                    "run_id": "run-1",
                    "question": "q",
                    "status": "completed",
                    "result": {"answer": "a"},
                    "error": None,
                    "created_at": "2026-05-27T00:00:00+00:00",
                    "updated_at": "2026-05-27T00:00:00+00:00",
                },
            )

        client = PrimeSwarmHttpClient(
            "http://api.test",
            api_key="secret",
            transport=httpx.MockTransport(handler),
        )

        payload = client.create_run("q", source_path="docs", use_web_search=True, top_k=3)

        self.assertEqual(payload["run_id"], "run-1")
        self.assertEqual(seen, {"path": "/v1/runs", "api_key": "secret"})
        self.assertEqual(body, {"question": "q", "source_path": "docs", "top_k": 3, "use_web_search": True})

    def test_http_client_raises_helpful_status_error(self) -> None:
        client = PrimeSwarmHttpClient(
            "http://api.test",
            transport=httpx.MockTransport(lambda request: httpx.Response(401, json={"detail": "invalid api key"})),
        )

        with self.assertRaisesRegex(CliHttpError, "401: invalid api key"):
            client.create_run("q")


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


class TestLocalResearchRetrieval(unittest.TestCase):
    def test_run_research_uses_local_sources_as_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "rules.md"
            source.write_text(
                "# Heist Manifest\nSteal patterns, not packages.\nCredit sources in docs.",
                encoding="utf-8",
            )

            record = asyncio.run(run_research("What do we steal?", InMemoryRunStore(), source_path=source))

        self.assertEqual(record.status, "completed")
        self.assertIn("Steal patterns", record.result["evidence"])
        self.assertEqual(record.result["sources"][0]["title"], "Heist Manifest")


class TestExternalWebSearch(unittest.TestCase):
    def test_run_research_uses_ranked_web_search_results(self) -> None:
        provider = StaticSearchProvider(
            [
                SearchResult(
                    url="https://medium.com/noisy",
                    title="Noisy blog",
                    snippet="Less authoritative note.",
                    score=0.9,
                ),
                SearchResult(
                    url="https://docs.example.com/official",
                    title="Official docs",
                    snippet="Authoritative web evidence.",
                    score=0.6,
                ),
            ]
        )

        record = asyncio.run(
            run_research("What is authoritative?", InMemoryRunStore(), search_provider=provider, use_web_search=True)
        )

        self.assertEqual(record.status, "completed")
        self.assertIn("Authoritative web evidence", record.result["evidence"])
        self.assertEqual(record.result["sources"][0]["title"], "Official docs")

    def test_http_json_search_provider_parses_results(self) -> None:
        seen: dict[str, object] = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            seen["authorization"] = request.headers["authorization"]
            seen["body"] = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "url": "https://example.com/a",
                            "title": "A",
                            "snippet": "Alpha",
                            "score": 0.4,
                            "published_date": "2026-05-20",
                        }
                    ]
                },
            )

        provider = HTTPJSONSearchProvider(
            "https://search.example.test/query",
            api_key="search-key",
            transport=httpx.MockTransport(handler),
        )

        results = asyncio.run(provider.search("alpha", k=2))

        self.assertEqual(results[0].url, "https://example.com/a")
        self.assertEqual(seen["authorization"], "Bearer search-key")
        self.assertEqual(seen["body"], {"query": "alpha", "k": 2})


if __name__ == "__main__":
    unittest.main()
