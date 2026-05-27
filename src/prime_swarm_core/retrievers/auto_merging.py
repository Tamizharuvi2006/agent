"""LlamaIndex-inspired auto-merging retriever."""

from __future__ import annotations

from collections import defaultdict

from prime_swarm_core.data.document import Document
from prime_swarm_core.retrievers.base import Retriever


class AutoMergingRetriever:
    """Return parent docs when enough child chunks from the same parent match."""

    def __init__(
        self,
        child_retriever: Retriever,
        parent_documents: dict[str, Document],
        *,
        parent_threshold: int = 3,
    ) -> None:
        if parent_threshold <= 0:
            raise ValueError("parent_threshold must be positive")
        self.child_retriever = child_retriever
        self.parent_documents = dict(parent_documents)
        self.parent_threshold = parent_threshold

    async def retrieve(self, query: str, k: int = 10) -> list[Document]:
        child_hits = await self.child_retriever.retrieve(query, k=max(k * self.parent_threshold, k))
        groups: dict[str, list[Document]] = defaultdict(list)
        ungrouped: list[Document] = []

        for document in child_hits:
            parent_id = document.metadata.get("parent_id")
            if parent_id is None:
                ungrouped.append(document)
            else:
                groups[str(parent_id)].append(document)

        merged: list[Document] = []
        emitted_parents: set[str] = set()
        for document in child_hits:
            parent_id = document.metadata.get("parent_id")
            if parent_id is None:
                if document not in merged:
                    merged.append(document)
                continue

            parent_key = str(parent_id)
            siblings = groups[parent_key]
            if len(siblings) >= self.parent_threshold and parent_key in self.parent_documents:
                if parent_key not in emitted_parents:
                    merged.append(
                        self.parent_documents[parent_key].with_metadata(
                            merged_from_children=len(siblings),
                            parent_id=parent_key,
                        )
                    )
                    emitted_parents.add(parent_key)
            elif document not in merged:
                merged.append(document)

            if len(merged) >= k:
                break

        return merged[:k]

