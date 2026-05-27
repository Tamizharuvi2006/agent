"""Shared document shape for ingestion and retrieval."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True, slots=True)
class Document:
    page_content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_metadata(self, **metadata: Any) -> "Document":
        next_metadata = dict(self.metadata)
        next_metadata.update(metadata)
        return replace(self, metadata=next_metadata)

