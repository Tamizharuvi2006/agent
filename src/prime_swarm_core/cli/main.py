"""Typer CLI for local product workflows."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import typer

from prime_swarm_core.cli.config import CliConfigError, CliProfile, load_profile
from prime_swarm_core.cli.http_client import CliHttpError, PrimeSwarmHttpClient
from prime_swarm_core.product import InMemoryRunStore, SQLiteRunStore, run_research


app = typer.Typer(help="PRIME-SWARM-CORE CLI")


@app.command()
def health(
    api_url: str | None = typer.Option(None, "--api-url", help="Call a running API service."),
    profile: str | None = typer.Option(None, "--profile", help="Read defaults from this config profile."),
    config: Path | None = typer.Option(None, "--config", help="Path to a JSON config file."),
) -> None:
    """Print CLI health."""
    profile_config = _profile(profile, config)
    resolved_api_url = api_url or os.getenv("PRIME_SWARM_API_URL") or profile_config.api_url
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
    web: bool = typer.Option(False, "--web", help="Use configured external web search."),
    top_k: int | None = typer.Option(None, "--top-k", min=1, max=20, help="Number of source chunks to retrieve."),
    profile: str | None = typer.Option(None, "--profile", help="Read defaults from this config profile."),
    config: Path | None = typer.Option(None, "--config", help="Path to a JSON config file."),
) -> None:
    """Run a mock-backed local research flow."""
    profile_config = _profile(profile, config)
    resolved_api_url = api_url or os.getenv("PRIME_SWARM_API_URL") or profile_config.api_url
    resolved_api_key = api_key or os.getenv("PRIME_SWARM_API_KEY") or profile_config.api_key or "dev-key"
    resolved_db = db or profile_config.db
    resolved_source = source or profile_config.source
    resolved_web = web or profile_config.web
    resolved_top_k = top_k or profile_config.top_k or 4

    async def _run() -> None:
        if resolved_api_url:
            record = PrimeSwarmHttpClient(
                resolved_api_url,
                api_key=resolved_api_key,
            ).create_run(
                question,
                source_path=str(resolved_source) if resolved_source else None,
                use_web_search=resolved_web,
                top_k=resolved_top_k,
            )
            output = record
        else:
            store = SQLiteRunStore(resolved_db) if resolved_db else InMemoryRunStore()
            output = (
                await run_research(
                    question,
                    store,
                    source_path=resolved_source,
                    use_web_search=resolved_web,
                    top_k=resolved_top_k,
                )
            ).as_dict()
        if json_output:
            typer.echo(json.dumps(output, sort_keys=True))
        else:
            typer.echo(output.get("result", {}).get("answer", ""))

    try:
        asyncio.run(_run())
    except CliHttpError as exc:
        raise typer.BadParameter(str(exc), param_hint="--api-url") from exc


def _profile(name: str | None, config: Path | None) -> CliProfile:
    try:
        return load_profile(name, config)
    except CliConfigError as exc:
        raise typer.BadParameter(str(exc), param_hint="--profile") from exc


if __name__ == "__main__":
    app()
