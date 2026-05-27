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
    browser_url: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_base_url: str | None = None
    llm: bool = False
    web: bool = False
    top_k: int | None = None


@dataclass(frozen=True, slots=True)
class CliProfileUpdate:
    api_url: str | None = None
    api_key: str | None = None
    db: Path | None = None
    source: Path | None = None
    browser_url: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_base_url: str | None = None
    llm: bool | None = None
    web: bool | None = None
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


def save_profile(name: str, update: CliProfileUpdate, path: str | Path | None = None) -> Path:
    config_path = Path(path).expanduser() if path else default_config_path()
    data: dict[str, Any] = {"profiles": {}}
    if config_path.exists():
        data = _load_json(config_path)

    profiles = data.setdefault("profiles", {})
    if not isinstance(profiles, dict):
        raise CliConfigError("config must contain a profiles object")

    current = profiles.get(name, {})
    if not isinstance(current, dict):
        raise CliConfigError(f"profile is not an object: {name}")

    next_profile = dict(current)
    next_profile.update(_update_to_dict(update))
    profiles[name] = next_profile

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return config_path


def list_profiles(path: str | Path | None = None) -> list[str]:
    config_path = Path(path).expanduser() if path else default_config_path()
    if not config_path.exists():
        return []
    data = _load_json(config_path)
    profiles = data.get("profiles")
    if not isinstance(profiles, dict):
        raise CliConfigError("config must contain a profiles object")
    return sorted(str(name) for name in profiles)


def delete_profile(name: str, path: str | Path | None = None) -> Path:
    config_path = Path(path).expanduser() if path else default_config_path()
    if not config_path.exists():
        raise CliConfigError(f"config file not found: {config_path}")

    data = _load_json(config_path)
    profiles = data.get("profiles")
    if not isinstance(profiles, dict):
        raise CliConfigError("config must contain a profiles object")
    if name not in profiles:
        raise CliConfigError(f"profile not found: {name}")

    del profiles[name]
    config_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return config_path


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
        browser_url=_optional_str(raw.get("browser_url")),
        llm_provider=_optional_str(raw.get("llm_provider")),
        llm_model=_optional_str(raw.get("llm_model")),
        llm_base_url=_optional_str(raw.get("llm_base_url")),
        llm=bool(raw.get("llm", False)),
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


def _update_to_dict(update: CliProfileUpdate) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if update.api_url is not None:
        data["api_url"] = update.api_url
    if update.api_key is not None:
        data["api_key"] = update.api_key
    if update.db is not None:
        data["db"] = str(update.db)
    if update.source is not None:
        data["source"] = str(update.source)
    if update.browser_url is not None:
        data["browser_url"] = update.browser_url
    if update.llm_provider is not None:
        data["llm_provider"] = update.llm_provider
    if update.llm_model is not None:
        data["llm_model"] = update.llm_model
    if update.llm_base_url is not None:
        data["llm_base_url"] = update.llm_base_url
    if update.llm is not None:
        data["llm"] = update.llm
    if update.web is not None:
        data["web"] = update.web
    if update.top_k is not None:
        if update.top_k < 1 or update.top_k > 20:
            raise CliConfigError("profile top_k must be between 1 and 20")
        data["top_k"] = update.top_k
    return data
