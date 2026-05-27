"""Semantic Kernel-inspired plugin folder loader."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class PluginDefinition:
    name: str
    path: Path
    schema: dict[str, Any]
    readme: str = ""
    examples: tuple[Path, ...] = field(default_factory=tuple)


def discover_plugins(root: str | Path) -> list[PluginDefinition]:
    root_path = Path(root).expanduser().resolve()
    if not root_path.exists():
        raise FileNotFoundError(str(root_path))
    if not root_path.is_dir():
        raise NotADirectoryError(str(root_path))

    plugins: list[PluginDefinition] = []
    for child in sorted(root_path.iterdir()):
        if child.is_dir() and (child / "schema.json").exists():
            plugins.append(load_plugin(child))
    return plugins


def load_plugin(path: str | Path) -> PluginDefinition:
    plugin_path = Path(path).expanduser().resolve()
    schema_path = plugin_path / "schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(str(schema_path))

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    name = str(schema.get("name") or plugin_path.name)
    readme_path = plugin_path / "README.md"
    examples_dir = plugin_path / "examples"
    examples = tuple(sorted(examples_dir.glob("*.json"))) if examples_dir.exists() else ()

    return PluginDefinition(
        name=name,
        path=plugin_path,
        schema=schema,
        readme=readme_path.read_text(encoding="utf-8") if readme_path.exists() else "",
        examples=examples,
    )

