"""Typer CLI for local product workflows."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import typer

from prime_swarm_core.cli.http_client import CliHttpError, PrimeSwarmHttpClient
from prime_swarm_core.product import InMemoryRunStore, SQLiteRunStore, run_research


app = typer.Typer(help="PRIME-SWARM-CORE CLI")


@app.command()
def health(api_url: str | None = typer.Option(None, "--api-url", help="Call a running API service.")) -> None:
    """Print CLI health."""
    resolved_api_url = api_url or os.getenv("PRIME_SWARM_API_URL")
    if resolved_api_url:
        try:
            payload = PrimeSwarmHttpClient(resolved_api_url).health()
        except CliHttpError as exc:
            raise typer.BadParameter(str(exc), param_hint="--api-url") from exc
        typer.echo(payload.get("status", "unknown"))
    else:
        typer.echo("ok")


@app.command()
def research(
    question: str,
    json_output: bool = typer.Option(False, "--json", help="Print raw JSON."),
    db: Path | None = typer.Option(None, "--db", help="Persist run records to this SQLite database."),
    api_url: str | None = typer.Option(None, "--api-url", help="Call a running API service."),
    api_key: str | None = typer.Option(None, "--api-key", help="API key for HTTP mode."),
    source: Path | None = typer.Option(None, "--source", help="Read evidence from this local file or directory."),
    top_k: int = typer.Option(4, "--top-k", min=1, max=20, help="Number of source chunks to retrieve."),
) -> None:
    """Run a mock-backed local research flow."""

    async def _run() -> None:
        resolved_api_url = api_url or os.getenv("PRIME_SWARM_API_URL")
        if resolved_api_url:
            record = PrimeSwarmHttpClient(
                resolved_api_url,
                api_key=api_key or os.getenv("PRIME_SWARM_API_KEY") or "dev-key",
            ).create_run(question, source_path=str(source) if source else None, top_k=top_k)
            output = record
        else:
            store = SQLiteRunStore(db) if db else InMemoryRunStore()
            output = (await run_research(question, store, source_path=source, top_k=top_k)).as_dict()
        if json_output:
            typer.echo(json.dumps(output, sort_keys=True))
        else:
            typer.echo(output.get("result", {}).get("answer", ""))

    try:
        asyncio.run(_run())
    except CliHttpError as exc:
        raise typer.BadParameter(str(exc), param_hint="--api-url") from exc


if __name__ == "__main__":
    app()
