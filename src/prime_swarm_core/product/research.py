"""Mock-backed research product service."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from prime_swarm_core.data import Document, load_directory, load_file, markdown_split, recursive_split
from prime_swarm_core.graph import Command, GraphRunner
from prime_swarm_core.llm import ChatModel, MockChatModel, call_signature, create_chat_model
from prime_swarm_core.product.browser import BrowserProvider, HTTPHTMLBrowserProvider
from prime_swarm_core.product.runs import RunRecord, RunStore
from prime_swarm_core.product.search import SearchProvider, SearchProviderNotConfigured
from prime_swarm_core.prompts import FieldSpec, Signature
from prime_swarm_core.quality import rerank_sources
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
    browser_url: str | None = None,
    browser_provider: BrowserProvider | None = None,
    search_provider: SearchProvider | None = None,
    chat_model: ChatModel | None = None,
    use_llm: bool = False,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_base_url: str | None = None,
    use_web_search: bool = False,
    top_k: int = 4,
) -> RunRecord:
    run_id = run_id or uuid4().hex
    created = RunRecord(run_id=run_id, question=question, status="running")
    await store.put(created)

    model = chat_model or _default_chat_model(
        question,
        use_llm=use_llm,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_base_url=llm_base_url,
    )
    signature = _signature()

    async def search_node(state):
        evidence, sources = await _retrieve_evidence(
            state.values["question"],
            source_path=source_path,
            browser_url=browser_url,
            browser_provider=browser_provider,
            search_provider=search_provider,
            use_web_search=use_web_search,
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


def _default_chat_model(
    question: str,
    *,
    use_llm: bool,
    llm_provider: str | None,
    llm_model: str | None,
    llm_base_url: str | None,
) -> ChatModel:
    if use_llm:
        return create_chat_model(provider=llm_provider, model=llm_model, base_url=llm_base_url)
    return MockChatModel([{"answer": f"Mock research answer for: {question}", "confidence": 0.8}])


async def _retrieve_evidence(
    question: str,
    *,
    source_path: str | Path | None,
    browser_url: str | None,
    browser_provider: BrowserProvider | None,
    search_provider: SearchProvider | None,
    use_web_search: bool,
    top_k: int,
) -> tuple[str, list[dict[str, object]]]:
    if browser_url:
        return await _retrieve_browser_evidence(browser_url, browser_provider=browser_provider)

    if use_web_search:
        return await _retrieve_web_evidence(question, search_provider=search_provider, top_k=top_k)

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


async def _retrieve_browser_evidence(
    browser_url: str,
    *,
    browser_provider: BrowserProvider | None,
) -> tuple[str, list[dict[str, object]]]:
    provider = browser_provider or HTTPHTMLBrowserProvider()
    page = await provider.fetch(browser_url)
    evidence = f"[1] {page.title}: {page.text}"
    sources: list[dict[str, object]] = [
        {
            "source": page.url,
            "title": page.title,
            "rank": 1,
            "kind": "browser",
        }
    ]
    return evidence, sources


async def _retrieve_web_evidence(
    question: str,
    *,
    search_provider: SearchProvider | None,
    top_k: int,
) -> tuple[str, list[dict[str, object]]]:
    if search_provider is None:
        raise SearchProviderNotConfigured("web search requested but no search provider is configured")

    results = await search_provider.search(question, k=top_k)
    ranked = rerank_sources(results, needs_freshness=True)[:top_k]
    if not ranked:
        return (
            f"No web search results matched the question: {question}",
            [{"source": "web://empty", "title": "No matching web result", "rank": 1}],
        )

    evidence_lines: list[str] = []
    sources: list[dict[str, object]] = []
    for index, result in enumerate(ranked, start=1):
        evidence_lines.append(f"[{index}] {result.title}: {result.snippet} ({result.url})")
        sources.append(
            {
                "source": result.url,
                "title": result.title,
                "rank": index,
                "score": result.score,
            }
        )
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
