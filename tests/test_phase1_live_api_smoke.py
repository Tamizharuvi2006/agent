from __future__ import annotations

import json
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest

import httpx
from typer.testing import CliRunner
import uvicorn

from prime_swarm_core.api import create_app
from prime_swarm_core.cli.main import app as cli_app
from prime_swarm_core.product import InMemoryRunStore


class LiveUvicornServer:
    def __init__(self) -> None:
        self.port = _free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        config = uvicorn.Config(
            create_app(InMemoryRunStore()),
            host="127.0.0.1",
            port=self.port,
            log_level="critical",
            lifespan="off",
        )
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)

    def __enter__(self) -> "LiveUvicornServer":
        self.thread.start()
        self._wait_until_ready()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.server.should_exit = True
        self.thread.join(timeout=5)

    def _wait_until_ready(self) -> None:
        deadline = time.time() + 5
        last_error: Exception | None = None
        while time.time() < deadline:
            try:
                response = httpx.get(f"{self.url}/health", timeout=0.5)
                if response.status_code == 200:
                    return
            except httpx.HTTPError as exc:
                last_error = exc
            time.sleep(0.05)
        raise RuntimeError(f"Uvicorn smoke server did not become ready: {last_error}")


class TestPhase1LiveApiSmoke(unittest.TestCase):
    def test_live_uvicorn_api_and_http_cli(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "brief.md"
            source.write_text("# Runtime\nLocal retrieval feeds the research graph.", encoding="utf-8")

            with LiveUvicornServer() as server:
                response = httpx.post(
                    f"{server.url}/v1/runs",
                    headers={"x-api-key": "dev-key"},
                    json={"question": "What feeds the graph?", "source_path": str(source)},
                    timeout=5,
                )
                api_payload = response.json()

                cli_result = runner.invoke(
                    cli_app,
                    [
                        "research",
                        "What feeds the graph?",
                        "--source",
                        str(source),
                        "--api-url",
                        server.url,
                        "--api-key",
                        "dev-key",
                        "--json",
                    ],
                )
                cli_payload = json.loads(cli_result.stdout)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Local retrieval feeds", api_payload["result"]["evidence"])
        self.assertEqual(cli_result.exit_code, 0)
        self.assertIn("Local retrieval feeds", cli_payload["result"]["evidence"])


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


if __name__ == "__main__":
    unittest.main()
