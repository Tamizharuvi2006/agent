"""Local document loaders.

These are intentionally small, dependency-light loaders. More specialized
loaders can be added when the project has concrete ingestion use cases.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from prime_swarm_core.data.document import Document


TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".rst", ".log", ".py", ".js", ".ts", ".json", ".csv"}


def load_text(path: str | Path, *, encoding: str = "utf-8") -> list[Document]:
    file_path = _resolve_file(path)
    content = file_path.read_text(encoding=encoding)
    return [
        Document(
            page_content=content,
            metadata={
                "source": str(file_path),
                "loader": "text",
                "file_name": file_path.name,
                "file_suffix": file_path.suffix.lower(),
            },
        )
    ]


def load_json(path: str | Path, *, encoding: str = "utf-8") -> list[Document]:
    file_path = _resolve_file(path)
    data = json.loads(file_path.read_text(encoding=encoding))
    return [
        Document(
            page_content=json.dumps(data, indent=2, sort_keys=True),
            metadata={
                "source": str(file_path),
                "loader": "json",
                "file_name": file_path.name,
                "file_suffix": file_path.suffix.lower(),
                "json_type": type(data).__name__,
            },
        )
    ]


def load_csv(path: str | Path, *, encoding: str = "utf-8") -> list[Document]:
    file_path = _resolve_file(path)
    with file_path.open("r", encoding=encoding, newline="") as handle:
        rows = list(csv.DictReader(handle))

    documents: list[Document] = []
    for index, row in enumerate(rows):
        clean_row = {key: value for key, value in row.items() if key is not None}
        content = "\n".join(f"{key}: {value}" for key, value in clean_row.items())
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": str(file_path),
                    "loader": "csv",
                    "file_name": file_path.name,
                    "file_suffix": file_path.suffix.lower(),
                    "row_index": index,
                    "columns": list(clean_row.keys()),
                },
            )
        )
    return documents


def load_directory(
    path: str | Path,
    *,
    recursive: bool = True,
    encoding: str = "utf-8",
    suffixes: set[str] | None = None,
) -> list[Document]:
    directory = Path(path).expanduser().resolve()
    if not directory.exists():
        raise FileNotFoundError(str(directory))
    if not directory.is_dir():
        raise NotADirectoryError(str(directory))

    allowed_suffixes = {suffix.lower() for suffix in (suffixes or TEXT_SUFFIXES)}
    pattern = "**/*" if recursive else "*"
    documents: list[Document] = []

    for file_path in sorted(directory.glob(pattern)):
        if not file_path.is_file() or file_path.suffix.lower() not in allowed_suffixes:
            continue
        documents.extend(load_file(file_path, encoding=encoding))
    return documents


def load_file(path: str | Path, *, encoding: str = "utf-8") -> list[Document]:
    file_path = _resolve_file(path)
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        return load_json(file_path, encoding=encoding)
    if suffix == ".csv":
        return load_csv(file_path, encoding=encoding)
    return load_text(file_path, encoding=encoding)


def _resolve_file(path: str | Path) -> Path:
    file_path = Path(path).expanduser().resolve()
    if not file_path.exists():
        raise FileNotFoundError(str(file_path))
    if not file_path.is_file():
        raise IsADirectoryError(str(file_path))
    return file_path

