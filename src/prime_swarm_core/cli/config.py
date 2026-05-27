"""JSON config profiles for the CLI."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any


CONFIG_ENV_VAR = "PRIME_SWARM_CONFIG"


class CliConfigError(ValueError):
    """Raised when a CLI config file is invalid."""


@dataclass(frozen=True, slots=True)
class CliProfile:
    api_url: str | None = None
    api_key: str | None = None
    db: Path | None = None
    source: Path | None = None
    web: bool = False
    top_k: int | None = None


def default_config_path() -> Path:
    configured = os.getenv(CONFIG_ENV_VAR)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".prime-swarm" / "config.json"


def load_profile(name: str | None, path: str | Path | None = None) -> CliProfile:
    if name is None:
        return CliProfile()

    config_path = Path(path).expanduser() if path else default_config_path()
    if not config_path.exists():
        raise CliConfigError(f"config file not found: {config_path}")

    data = _load_json(config_path)
    profiles = data.get("profiles")
    if not isinstance(profiles, dict):
        raise CliConfigError("config must contain a profiles object")

    raw_profile = profiles.get(name)
    if not isinstance(raw_profile, dict):
        raise CliConfigError(f"profile not found: {name}")
    return _parse_profile(raw_profile)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CliConfigError(f"invalid JSON config: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise CliConfigError("config root must be an object")
    return data


def _parse_profile(raw: dict[str, Any]) -> CliProfile:
    top_k = raw.get("top_k")
    if top_k is not None:
        top_k = int(top_k)
        if top_k < 1 or top_k > 20:
            raise CliConfigError("profile top_k must be between 1 and 20")

    return CliProfile(
        api_url=_optional_str(raw.get("api_url")),
        api_key=_optional_str(raw.get("api_key")),
        db=_optional_path(raw.get("db")),
        source=_optional_path(raw.get("source")),
        web=bool(raw.get("web", False)),
        top_k=top_k,
    )


def _optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _optional_path(value: Any) -> Path | None:
    if value in (None, ""):
        return None
    return Path(str(value)).expanduser()
