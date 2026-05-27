"""Small local text splitters."""

from __future__ import annotations

import re

from prime_swarm_core.data.document import Document


def recursive_split(
    doc: Document,
    *,
    chunk_size: int = 1000,
    overlap: int = 100,
) -> list[Document]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    text = doc.page_content
    if len(text) <= chunk_size:
        return [doc.with_metadata(chunk_index=0, chunk_start=0, chunk_end=len(text))]

    chunks: list[Document] = []
    start = 0
    index = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            split_at = _best_boundary(text, start, end)
            if split_at > start:
                end = split_at
        content = text[start:end].strip()
        if content:
            chunks.append(
                Document(
                    page_content=content,
                    metadata={
                        **doc.metadata,
                        "chunk_index": index,
                        "chunk_start": start,
                        "chunk_end": end,
                    },
                )
            )
            index += 1
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def markdown_split(doc: Document) -> list[Document]:
    sections = re.split(r"(?m)^(#{1,6}\s+.+)$", doc.page_content)
    if len(sections) == 1:
        return [doc.with_metadata(section_index=0)]

    chunks: list[Document] = []
    preamble = sections[0].strip()
    if preamble:
        chunks.append(Document(preamble, {**doc.metadata, "section_index": 0}))

    section_index = len(chunks)
    for heading, body in zip(sections[1::2], sections[2::2], strict=False):
        content = f"{heading}\n{body}".strip()
        if content:
            chunks.append(
                Document(
                    content,
                    {
                        **doc.metadata,
                        "section_index": section_index,
                        "heading": heading.lstrip("#").strip(),
                    },
                )
            )
            section_index += 1
    return chunks


def _best_boundary(text: str, start: int, end: int) -> int:
    window = text[start:end]
    for separator in ("\n\n", "\n", ". ", " "):
        pos = window.rfind(separator)
        if pos > max(0, len(window) // 2):
            return start + pos + len(separator)
    return end

