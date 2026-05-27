"""Typer CLI for local product workflows."""

from __future__ import annotations

import asyncio
import json

import typer

from prime_swarm_core.product import InMemoryRunStore, run_research


app = typer.Typer(help="PRIME-SWARM-CORE CLI")


@app.command()
def health() -> None:
    """Print CLI health."""
    typer.echo("ok")


@app.command()
def research(question: str, json_output: bool = typer.Option(False, "--json", help="Print raw JSON.")) -> None:
    """Run a mock-backed local research flow."""

    async def _run() -> None:
        record = await run_research(question, InMemoryRunStore())
        if json_output:
            typer.echo(json.dumps(record.as_dict(), sort_keys=True))
        else:
            typer.echo(record.result.get("answer", ""))

    asyncio.run(_run())


if __name__ == "__main__":
    app()
