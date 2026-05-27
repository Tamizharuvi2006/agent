"""Mock-backed research product service."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from prime_swarm_core.data import Document, load_directory, load_file, markdown_split, recursive_split
from prime_swarm_core.graph import Command, GraphRunner
from prime_swarm_core.llm import MockChatModel, call_signature
from prime_swarm_core.product.runs import RunRecord, RunStore
from prime_swarm_core.prompts import FieldSpec, Signature
from prime_swarm_core.retrievers import InMemoryKeywordRetriever


def _signature() -> Signature:
    return Signature(
        name="research_answer",
        instruction="Answer the research question from the evidence in one sentence.",
        input_fields=(FieldSpec("question", str), FieldSpec("evidence", str),),
        output_fields=(FieldSpec("answer", str), FieldSpec("confidence", float),),
    )


async def run_research(
    question: str,
    store: RunStore,
    *,
    run_id: str | None = None,
    source_path: str | Path | None = None,
    top_k: int = 4,
) -> RunRecord:
    run_id = run_id or uuid4().hex
    created = RunRecord(run_id=run_id, question=question, status="running")
    await store.put(created)

    model = MockChatModel([{"answer": f"Mock research answer for: {question}", "confidence": 0.8}])
    signature = _signature()

    async def search_node(state):
        evidence, sources = await _retrieve_evidence(
            state.values["question"],
            source_path=source_path,
            top_k=top_k,
        )
        return Command.to("summarize", evidence=evidence, sources=sources)

    async def summarize_node(state):
        output = await call_signature(
            model,
            signature,
            question=state.values["question"],
            evidence=state.values["evidence"],
        )
        return Command.to(None, **output)

    try:
        result = await GraphRunner({"search": search_node, "summarize": summarize_node}).run(
            run_id,
            start_at="search",
            initial_values={"question": question},
        )
        completed = replace(
            created,
            status="completed",
            result=result.state.values,
            updated_at=datetime.now(timezone.utc),
        )
        await store.put(completed)
        return completed
    except Exception as exc:
        failed = replace(created, status="failed", error=str(exc), updated_at=datetime.now(timezone.utc))
        await store.put(failed)
        return failed


async def _retrieve_evidence(
    question: str,
    *,
    source_path: str | Path | None,
    top_k: int,
) -> tuple[str, list[dict[str, object]]]:
    if source_path is None:
        sources = [
            {"source": "mock://official", "title": "Official-style source", "rank": 1},
            {"source": "mock://background", "title": "Background note", "rank": 2},
        ]
        evidence = [
            f"Official-style source for {question}",
            f"Background note for {question}",
        ]
        return "\n".join(evidence), sources

    documents = _load_source_documents(source_path)
    chunks = _split_documents(documents)
    retrieved = await InMemoryKeywordRetriever(chunks).retrieve(question, k=top_k)
    if not retrieved:
        return (
            f"No local source matched the question: {question}",
            [{"source": str(Path(source_path)), "title": "No matching local source", "rank": 1}],
        )

    evidence_lines: list[str] = []
    sources: list[dict[str, object]] = []
    seen_sources: set[str] = set()
    for index, document in enumerate(retrieved, start=1):
        title = _title(document)
        source = str(document.metadata.get("source", source_path))
        evidence_lines.append(f"[{index}] {title}: {document.page_content}")
        if source not in seen_sources:
            sources.append(
                {
                    "source": source,
                    "title": title,
                    "rank": len(sources) + 1,
                    "chunk_index": document.metadata.get("chunk_index", document.metadata.get("section_index")),
                }
            )
            seen_sources.add(source)
    return "\n\n".join(evidence_lines), sources


def _load_source_documents(source_path: str | Path) -> list[Document]:
    path = Path(source_path).expanduser()
    if path.is_dir():
        return load_directory(path)
    return load_file(path)


def _split_documents(documents: list[Document]) -> list[Document]:
    chunks: list[Document] = []
    for document in documents:
        if str(document.metadata.get("file_suffix", "")).lower() in {".md", ".markdown"}:
            sections = markdown_split(document)
            for section in sections:
                chunks.extend(recursive_split(section, chunk_size=1200, overlap=120))
        else:
            chunks.extend(recursive_split(document, chunk_size=1200, overlap=120))
    return chunks


def _title(document: Document) -> str:
    heading = document.metadata.get("heading")
    if heading:
        return str(heading)
    file_name = document.metadata.get("file_name")
    if file_name:
        return str(file_name)
    return "Local source"
