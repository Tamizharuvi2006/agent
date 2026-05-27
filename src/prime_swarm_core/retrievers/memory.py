"""Small in-memory retriever for local testing and demos."""

from __future__ import annotations

import re
from dataclasses import dataclass

from prime_swarm_core.data.document import Document


@dataclass(frozen=True, slots=True)
class ScoredDocument:
    document: Document
    score: float


class InMemoryKeywordRetriever:
    def __init__(self, documents: list[Document]) -> None:
        self.documents = tuple(documents)

    async def retrieve(self, query: str, k: int = 10) -> list[Document]:
        terms = _terms(query)
        scored = [
            ScoredDocument(document=document, score=_score(document, terms))
            for document in self.documents
        ]
        ranked = sorted(scored, key=lambda item: item.score, reverse=True)
        return [item.document for item in ranked if item.score > 0][:k]


def _terms(text: str) -> set[str]:
    return {term.lower() for term in re.findall(r"[a-zA-Z0-9_]+", text) if len(term) > 1}


def _score(document: Document, terms: set[str]) -> float:
    if not terms:
        return 0.0
    content_terms = _terms(document.page_content)
    metadata_terms = _terms(" ".join(str(value) for value in document.metadata.values()))
    return len(terms & content_terms) + 0.25 * len(terms & metadata_terms)

