# 🦝 THE HEIST MANIFEST
## What We're Stealing From Every Major Agent Framework
### (And Why We're Not Just Importing Them)

> **Mission:** Build PRIME-SWARM-CORE v3 with the **best ideas** from the entire agent ecosystem — without inheriting their dependencies, bugs, lock-in, or bloat.
>
> **Rule:** Steal the *pattern*, not the *code*. Re-implement clean, in your style, in your codebase.

---

## 📋 Quick Index

| # | Framework | What We Steal | What We Leave |
|---|---|---|---|
| 1 | **LangGraph** | State graph + checkpointer + interrupts | Their runtime |
| 2 | **LangChain** | Document loaders + retriever interface + text splitters | Chains, agents, magic |
| 3 | **LangSmith** | Tracing + dataset + eval UI | Lock-in (use OTEL exporters) |
| 4 | **CrewAI** | Role/persona pattern + crew composition | Sequential-only execution |
| 5 | **AutoGen** | GroupChat debate + reflection pattern | Turn-based limitation |
| 6 | **DSPy** | Signatures + Optimizers (MIPRO/BootstrapFewShot) | DSPy runtime |
| 7 | **Pydantic AI** | Type-safe tool definitions + result validation | Their agent class |
| 8 | **Instructor** | Structured-output retry-with-validation pattern | Library dependency |
| 9 | **Haystack** | Pipeline node naming + branching component model | Their DAG runtime |
| 10 | **LlamaIndex** | Hierarchical retriever + auto-merging chunks | Their query engine |
| 11 | **Semantic Kernel** | Skills/plugins folder convention + planner separation | C#-isms |
| 12 | **OpenAI Swarm** | Handoff primitive + agent transfer | Their stateless model |
| 13 | **Agno (Phidata)** | Memory + storage + tools as composable mixins | Their UI |
| 14 | **Smol Agents** | Code-as-action (ReAct via Python code) | Sandbox risk |
| 15 | **MetaGPT** | SOP (Standard Operating Procedure) prompts per role | Software-team metaphor |
| 16 | **Temporal** | Workflow determinism + signals + activities | Nothing — use them |
| 17 | **Browser-Use** | Page-as-DOM-tree LLM input format | Their executor |
| 18 | **Perplexity / Exa** | Source whitelist + freshness ranking + cite-as-you-go | Closed product |
| 19 | **Cursor / Aider** | Diff-based file editing + plan-then-act | IDE coupling |
| 20 | **Mastra (TS)** | Workflow `.step().then().branch()` ergonomic API | TS-only |

---

## 1. 🕸️ LangGraph — *State Graph + Checkpointer*

### Steal
- **State as a typed dataclass** flowing through nodes (not a magic dict). You're already doing this with `RunContext`.
- **`Command` pattern** for nodes returning `{goto: "next_node", update: {...}}`. Cleaner than your current `(new_state, ctx)` tuple returns.
- **Checkpointer interface** — pluggable persistence (SQLite/Postgres/Redis). Yours is checkpoint.py; standardize the interface to match: `get()`, `put()`, `list()`.
- **`interrupt()` primitive** — a node can pause execution and wait for human input. **This is exactly your HITL gate** but as a clean primitive.
- **Subgraph composition** — a node can BE another graph. Your recursive sub-DAGs already do this — formalize the API.
- **Streaming via async generators** — yield events as you go.

### Leave
- LangGraph runtime itself (you have one)
- `langchain-core` dependency chain
- LangSmith coupling

### Implementation in your repo
```python
# packages/core/graph/command.py
@dataclass
class Command:
    goto: str | None = None              # next node (None = stay)
    update: dict | None = None           # state delta
    interrupt: dict | None = None        # pause + payload for human
    send: list[Send] | None = None       # fan-out to N parallel nodes

# packages/core/graph/checkpointer.py
class Checkpointer(Protocol):
    async def get(self, run_id: str) -> RunState | None: ...
    async def put(self, run_id: str, state: RunState) -> None: ...
    async def list(self, run_id: str) -> list[RunState]: ...   # history

class PostgresCheckpointer(Checkpointer): ...
class SQLiteCheckpointer(Checkpointer): ...   # local dev
class RedisCheckpointer(Checkpointer): ...    # hot path cache

# packages/core/graph/interrupt.py
class HumanInterrupt(Exception):
    def __init__(self, payload: dict): self.payload = payload
```

---

## 2. 🧱 LangChain — *Loaders + Splitters + Retriever Interface*

### Steal
- **`Document` dataclass** — `{page_content: str, metadata: dict}`. Universal data shape.
- **Document loaders pattern**: `WebLoader`, `PDFLoader`, `YouTubeLoader`, `NotionLoader`, `GitHubLoader`, `S3Loader`. Each is just a function returning `list[Document]`.
- **Text splitters**: recursive character, semantic, markdown-aware, code-aware. Your worker truncates raw — splitters are smarter.
- **Retriever interface**: `async def aget_relevant_documents(query) -> list[Document]`. Lets you swap Qdrant/Chroma/BM25 transparently.

### Leave
- `Chain`, `LLMChain`, `AgentExecutor` — all of it
- The Runnable Lang abstraction
- 200MB of transitive deps

### Implementation
```python
# packages/core/data/document.py
@dataclass
class Document:
    page_content: str
    metadata: dict = field(default_factory=dict)

# packages/core/data/loaders/   ← one file per loader
async def load_url(url: str) -> list[Document]: ...
async def load_pdf(path: str) -> list[Document]: ...
async def load_youtube(video_url: str) -> list[Document]: ...

# packages/core/data/splitters.py
def recursive_split(doc: Document, chunk_size=1000, overlap=100) -> list[Document]: ...
def semantic_split(doc: Document, threshold=0.75) -> list[Document]: ...
def markdown_split(doc: Document) -> list[Document]: ...

# packages/core/retrievers/base.py
class Retriever(Protocol):
    async def retrieve(self, query: str, k: int = 10) -> list[Document]: ...

class QdrantRetriever(Retriever): ...
class HybridRetriever(Retriever): ...   # vector + BM25
```

**Pro tip:** for tricky loaders (Notion API, GitHub OAuth), it's totally fine to `pip install langchain-community` *just for the loader function* and import only what you need. No runtime coupling.

---

## 3. 🔭 LangSmith — *Tracing & Eval Dataset Format*

### Steal
- **Trace = nested spans with input/output/metadata at each level.** Already your event log conceptually — formalize it.
- **Dataset format**: `{id, inputs, expected_outputs, metadata, tags}`. Use it for evals/regression sets.
- **Evaluator pattern**: a function `(run, example) → score{accuracy, relevance, ...}`. Composable.
- **Run = trace + scores + tags + timestamps.** Single object you can serialize, ship, replay.

### Leave
- LangSmith SaaS lock-in
- Their UI (build your own dashboard later, or use Phoenix/Langfuse OSS)

### Implementation
```python
# packages/core/tracing/span.py — wraps OpenTelemetry
class Span:
    def __init__(self, name, inputs=None, parent=None): ...
    def end(self, outputs=None, error=None): ...
    def add_event(self, name, **attrs): ...
    def add_score(self, name, value): ...

@contextmanager
def trace(name: str, **inputs):
    span = current_tracer().start_span(name, inputs=inputs)
    try: yield span
    finally: span.end()

# Use it:
with trace("worker.run_node", node_id=node.id, question=node.question) as span:
    result = await react_loop(node)
    span.end(outputs={"answer": result.answer, "tokens": result.tokens})
```

Use **Phoenix** (Arize, OSS) or **Langfuse** (OSS, self-hostable) as the UI — both ingest OTEL natively. Zero lock-in, free.

---

## 4. 👥 CrewAI — *Role + Persona + Crew Composition*

### Steal
- **Role dataclass**: `{name, goal, backstory, allowed_tools, model}`. Crisp way to specify "who this agent is."
- **Crew = ordered list of (Role, Task) pairs** with shared memory + delegation. Your Phase 5 Personas are exactly this.
- **`expected_output`** field on tasks — forces clarity about what "done" looks like for each step.

### Leave
- Their sequential-only execution (you have a real DAG)
- The Pydantic-everywhere ceremony

### Implementation
```python
# packages/core/roles/role.py
@dataclass
class Role:
    name: str                    # "skeptic", "historian", "quant"
    goal: str                    # one sentence
    backstory: str               # gives the LLM a persona
    allowed_tools: list[str]
    model: str
    temperature: float = 0.3
    max_iterations: int = 8

    def system_prompt(self) -> str:
        return PERSONA_TEMPLATE.format(**asdict(self))

# packages/core/roles/library.py — pre-built personas
SKEPTIC = Role(name="skeptic", goal="...", backstory="...", ...)
HISTORIAN = Role(...)
QUANT = Role(...)
DEVILS_ADVOCATE = Role(...)
```

---

## 5. 🗣️ AutoGen — *GroupChat + Reflection*

### Steal
- **GroupChat pattern**: N agents in a shared conversation with a `Manager` agent deciding who speaks next. **Perfect for your debate nodes.**
- **Reflection**: after an answer, send it back to the same agent with "critique your own answer, then revise." Cheaper than 2 separate agents.
- **Conversable agent**: every agent has a uniform `async def respond(messages) -> message` interface.

### Leave
- Turn-based / non-parallel execution model
- Their config-file ceremony

### Implementation
```python
# packages/core/debate/group_chat.py
class GroupChat:
    def __init__(self, roles: list[Role], manager: Role, max_rounds=4):
        self.roles, self.manager, self.max_rounds = roles, manager, max_rounds
        self.transcript = []

    async def run(self, topic: str) -> DebateResult:
        for _ in range(self.max_rounds):
            next_speaker = await self._pick_speaker(topic)
            msg = await next_speaker.respond(self.transcript)
            self.transcript.append((next_speaker.name, msg))
            if self._consensus_reached(): break
        return await self._synthesize()

# packages/core/agents/reflection.py
async def reflect_and_revise(agent, initial_answer, criteria):
    critique = await agent.respond([
        {"role":"user","content":f"Critique this answer against: {criteria}\n\n{initial_answer}"}])
    revised = await agent.respond([
        {"role":"user","content":f"Revise based on critique:\n{critique}"}])
    return revised
```

---

## 6. 🎓 DSPy — *Signatures + Optimizers*

### Steal
- **Signature = typed I/O contract** for an LLM call:
  ```python
  class Summarize(Signature):
      """Summarize a research finding."""
      observation: str = InputField()
      summary: str = OutputField(desc="2-3 sentences")
      confidence: float = OutputField(ge=0, le=1)
  ```
- **BootstrapFewShot**: auto-generate few-shot examples from your eval set. Massively boosts quality.
- **MIPRO optimizer**: auto-rewrites prompts based on eval scores. Your Phase 6 prompt evolution — but smarter.

### Leave
- DSPy's heavyweight runtime
- Their teleprompter abstractions

### Implementation
```python
# packages/core/prompts/signature.py
@dataclass
class Signature:
    instruction: str
    input_fields: dict[str, type]
    output_fields: dict[str, type]

    def render_prompt(self, **inputs) -> str: ...
    def parse_output(self, text: str) -> dict: ...

# packages/observatory/optimizers/bootstrap.py
async def bootstrap_few_shot(signature, train_set, eval_fn, k=8):
    """Generate k high-quality examples from training data."""
    successful = []
    for example in train_set:
        output = await call_llm(signature, **example.inputs)
        if eval_fn(output, example.expected) > 0.8:
            successful.append((example.inputs, output))
        if len(successful) >= k: break
    return successful  # inject into prompt as few-shot

# packages/observatory/optimizers/mipro.py
async def optimize_prompt(signature, eval_set, n_candidates=5):
    """Generate prompt variants, eval each, keep winner."""
    variants = await generate_variants(signature.instruction, n=n_candidates)
    scored = [(v, await score_on_set(v, eval_set)) for v in variants]
    return max(scored, key=lambda x: x[1])[0]
```

---

## 7. 🎯 Pydantic AI — *Typed Tools + Result Validation*

### Steal
- **Tools defined as plain async functions with Pydantic argument models** — auto-generates JSON schema for OpenRouter.
- **`Result` model validation** — LLM output is parsed into a Pydantic model; on validation fail, automatic retry with error feedback.
- **`@tool` decorator** that registers schema + docstring + function.

### Leave
- Their Agent class
- Their dependency injection ceremony

### Implementation
```python
# packages/core/tools/decorator.py
def tool(name: str = None, allowed_in: list[str] = None):
    def decorator(fn):
        sig = inspect.signature(fn)
        schema = pydantic_schema_from_signature(sig)
        TOOLS[name or fn.__name__] = {
            "fn": fn, "schema": schema, "doc": fn.__doc__,
            "allowed_in": allowed_in or ["*"]
        }
        return fn
    return decorator

# Usage:
class SearchArgs(BaseModel):
    query: str
    num: int = Field(default=10, ge=1, le=20)
    site: str | None = None

@tool(name="web_search", allowed_in=["research", "news"])
async def web_search(args: SearchArgs) -> SearchResult:
    """Google web search via Serper."""
    return await serper.search(args.query, num=args.num, site=args.site)
```

---

## 8. 🔁 Instructor — *Retry-on-Validation-Failure*

### Steal
- **Pattern**: ask LLM for structured output → validate with Pydantic → if validation fails, send error back as a new user message → retry up to N times.
- Surprisingly powerful. ~99% success rate on structured extraction.

### Leave
- The library itself (it's small but you don't need it)

### Implementation
```python
# packages/core/llm/structured.py
async def call_structured(model, prompt, output_model: type[BaseModel],
                           max_retries=3) -> BaseModel:
    messages = [{"role":"user","content": prompt}]
    for attempt in range(max_retries):
        resp = await openrouter.chat(model, messages, json_mode=True)
        text = resp["choices"][0]["message"]["content"]
        try:
            return output_model.model_validate_json(text)
        except ValidationError as e:
            messages.append({"role":"assistant","content": text})
            messages.append({"role":"user","content":
                f"Your output failed validation:\n{e}\n\nReturn corrected JSON."})
    raise StructuredCallFailed(f"After {max_retries} attempts")
```

---

## 9. 🔗 Haystack — *Pipeline Node Naming Convention*

### Steal
- **Components have `inputs` and `outputs` declared as typed kwargs.** Engine wires them automatically by name + type.
- **Branching components**: a node can have `outputs={"answer": str, "needs_more_research": bool}` and the engine routes based on which output is populated.

### Leave
- Their YAML pipeline config (use Python)
- Their custom DAG runtime

### Implementation
```python
# packages/core/graph/component.py
@dataclass
class Component:
    name: str
    inputs: dict[str, type]       # name → type
    outputs: dict[str, type]
    fn: Callable

@component(inputs={"query": str}, outputs={"answer": str, "low_confidence": bool})
async def research_node(query: str) -> dict:
    result = await worker.run(query)
    return {"answer": result.answer, "low_confidence": result.confidence < 0.6}

# Engine routes:  low_confidence=True → debate node;  False → next research node
```

---

## 10. 📚 LlamaIndex — *Hierarchical Retrieval*

### Steal
- **Auto-merging retriever**: store chunks AND their parents. Retrieve small chunks, but return parents when many siblings hit.
- **Hierarchical summary index**: doc → section summaries → chunk summaries. Query routes through the tree.
- **Sub-question query engine**: break query into sub-Qs, retrieve per-Q, combine. **You already do this in your planner — formalize the retrieval variant.**

### Leave
- LlamaIndex's heavy runtime
- Their `Settings.embed_model = ...` global config style

### Implementation
```python
# packages/core/retrievers/auto_merging.py
class AutoMergingRetriever:
    """Retrieve small chunks. If 3+ siblings hit, return parent instead."""
    def __init__(self, qdrant, parent_threshold=3): ...
    async def retrieve(self, query, k=10):
        chunks = await self.qdrant.search(query, k=k*3)
        grouped = groupby(chunks, key=lambda c: c.parent_id)
        return [parent_doc(pid) if len(list(g)) >= self.parent_threshold
                else top_n(list(g), 1) for pid, g in grouped][:k]
```

---

## 11. 🔌 Semantic Kernel — *Plugins Folder + Planner Separation*

### Steal
- **Plugins folder convention**: each tool lives in its own folder with `tool.py` + `schema.json` + `examples/`. Scannable, discoverable, easy to disable.
- **Planner is a separate concern from execution.** You have this already — good architecture pattern.

### Leave
- C# idioms
- Their Kernel object

### Implementation
```
packages/core/plugins/
├── web_search/
│   ├── tool.py
│   ├── schema.json          # JSON schema for LLM function-calling
│   ├── README.md            # human-readable docs
│   └── examples/
│       └── basic.json
├── extract_url/
│   └── ...
```

Plus a `plugin_loader.py` that auto-scans this directory at startup.

---

## 12. 🤝 OpenAI Swarm — *Handoff Primitive*

### Steal
- **`handoff(target_agent, context)` primitive** — current agent says "this isn't my job, pass to X with this context." Clean way to compose specialist agents.
- **Stateless agents** — agents don't hold conversation state; the orchestrator does. Way easier to test + parallelize.

### Leave
- Their toy-library status
- Lack of distributed support

### Implementation
```python
# packages/core/handoff.py
@dataclass
class Handoff:
    target_agent: str            # role name
    context: dict                # what to pass to the new agent
    reason: str                  # why we're handing off

# Worker can emit:
return WorkerOutput(
    answer=None,
    handoff=Handoff(target_agent="quant", context={"data": rows},
                    reason="needs statistical analysis")
)
```

---

## 13. 🧰 Agno (Phidata) — *Composable Mixins*

### Steal
- **Memory, Storage, Tools, Knowledge as composable mixins on an Agent.** Lets you `Agent(memory=PostgresMemory, knowledge=QdrantKnowledge, tools=[...])` without subclassing.
- **`add_history_to_messages=True`** — automatic conversation history threading.

### Leave
- Their built-in UI (you're API-only)
- Sometimes-quirky API ergonomics

### Implementation
```python
# packages/core/agents/composable.py
@dataclass
class Agent:
    role: Role
    memory: Memory | None = None         # injected
    knowledge: Retriever | None = None   # injected
    tools: list[Tool] = field(default_factory=list)
    storage: Storage | None = None

    async def respond(self, messages: list[Message]) -> Message:
        if self.knowledge:
            kb_hits = await self.knowledge.retrieve(messages[-1].content)
            messages = inject_context(messages, kb_hits)
        if self.memory:
            history = await self.memory.recall(messages[-1].content)
            messages = inject_history(messages, history)
        return await llm_call(self.role.model, messages, tools=self.tools)
```

---

## 14. 🐍 Smol Agents — *Code-as-Action*

### Steal
- **Instead of JSON tool calls, the LLM emits Python code that calls tools as functions.** More expressive (loops, conditionals, transformations).
- **Single-step ReAct** = "write code that uses these tools to answer."

### Leave
- Their sandbox approach (just use your existing `code_executor` carefully)
- Auto-`exec()` of LLM code without strict review

### Implementation
**Make this a feature flag per-node**. Default to JSON tools (safer). Power users enable code-as-action for complex data-massage nodes.

```python
# packages/core/agents/code_react.py
CODE_REACT_PROMPT = """
You are given these tools as Python functions:
  web_search(query: str) -> list[Result]
  extract_url(url: str) -> str
  ...

Write Python code that uses them to answer the question.
The last expression should be your final answer.
"""

async def code_react_worker(node):
    code = await llm.generate_code(node.question, available_tools=node.tools)
    result = await sandboxed_exec(code, available_tools=node.tools)
    return result
```

---

## 15. 👔 MetaGPT — *SOPs per Role*

### Steal
- **Standard Operating Procedure prompts**: each role has a detailed step-by-step procedure embedded in its system prompt. Not "be a researcher" but "step 1: identify entities; step 2: search each; step 3: cross-reference; step 4: cite."
- **Output templates per role** — strict format that downstream agents can parse.

### Leave
- The software-company metaphor (CTO / PM / Engineer / QA roles)
- The ZIP-file project output

### Implementation
Update your existing `prompts/*.txt` to include explicit SOPs:
```
prompts/worker/v2.txt:
═══ STANDARD OPERATING PROCEDURE ═══
1. Decompose the sub-question into atomic claims.
2. For each claim:
   a. Call memory_recall first.
   b. If miss → call web_search with 2-3 query variants.
   c. extract_url on top 2 results.
   d. Triangulate across sources.
3. Emit structured ResearchOutput with confidence per claim.
═════════════════════════════════════
```

---

## 16. ⏱️ Temporal — *Just use it, don't reinvent*

### Steal (use directly, no reimplementation)
- **Workflows + Activities + Signals + Queries + Versioning + Replay**
- **Cron workflows** for nightly evals
- **Continue-as-new** pattern for long-running workflows
- **Heartbeats** for long-running activities

### Leave
- Nothing — this is the one framework you should fully adopt

**Don't reinvent.** Use the SDK. Just follow determinism rules.

---

## 17. 🌐 Browser-Use — *DOM-as-LLM-Input Format*

### Steal
- **Convert page DOM to an LLM-friendly tree with element IDs**:
  ```
  [12] <button> "Sign in"
  [13] <input type="text" placeholder="Email">
  [14] <a href="/forgot"> "Forgot password?"
  ```
  Then LLM can say `click(12)` or `fill(13, "...")`. Way more reliable than CSS selectors.

### Leave
- Their executor (you have Playwright tier already)

### Implementation
```python
# packages/multimodal/browser/dom_view.py
async def dom_to_llm_view(page) -> tuple[str, dict]:
    """Returns (string_tree, id_to_element_map)."""
    elements = await page.evaluate(JS_EXTRACT_INTERACTIVE_ELEMENTS)
    tree = "\n".join(f"[{e['id']}] <{e['tag']}> {e['text']!r}" for e in elements)
    id_map = {e['id']: e['xpath'] for e in elements}
    return tree, id_map
```

---

## 18. 🔎 Perplexity / Exa — *Source Quality Heuristics*

### Steal
- **Source whitelist/boost**: `.gov`, `.edu`, official org domains rank first.
- **Freshness ranking**: recent results boosted for "current"/"latest" queries.
- **Cite-as-you-go**: every sentence in the final answer maps to a specific source span.
- **Domain blacklist**: known content farms (`*forbes.com/sites/`, AI listicles) penalized.

### Leave
- Closed-source secret sauce we can't see anyway

### Implementation
```python
# packages/core/quality/source_ranker.py
WHITELIST_BOOST = 0.3
BLACKLIST_PENALTY = 0.5
FRESH_WINDOW_DAYS = 90

def rerank(results: list[SearchResult], needs_freshness: bool) -> list[SearchResult]:
    for r in results:
        r.score = base_score(r)
        if domain_in_whitelist(r.url): r.score += WHITELIST_BOOST
        if domain_in_blacklist(r.url): r.score -= BLACKLIST_PENALTY
        if needs_freshness and r.date and (today - r.date).days > FRESH_WINDOW_DAYS:
            r.score -= 0.2
    return sorted(results, key=lambda r: -r.score)
```

---

## 19. ✏️ Cursor / Aider — *Plan-then-Act + Diffs*

### Steal
- **Plan mode then act mode**: show the user the plan, get approval, then execute. **You already have HITL.**
- **Diff-based edits**: when modifying a report (e.g. on user feedback), output a unified diff, not a full rewrite. Easier to review.

### Leave
- IDE coupling
- Repo-aware features (not relevant for research agent)

### Implementation
```python
# packages/api/routes/runs.py
@router.post("/v1/runs/{id}/revise")
async def revise_report(id: str, instructions: str):
    original = await get_report(id)
    diff = await reviser_agent.diff(original, instructions)
    return {"diff": diff, "preview_url": ..., "apply_endpoint": ...}
```

---

## 20. 🛠️ Mastra (TypeScript) — *Ergonomic Workflow API*

### Steal
- **Fluent workflow builder**:
  ```python
  workflow = (
    Workflow("research")
      .step("route", route_activity)
      .then("plan", plan_activity)
      .branch("hitl", on_interactive=True, then="hitl_gate")
      .parallel("execute", [research_node, debate_node])
      .then("synthesize", synthesize_activity)
      .build()
  )
  ```
- More readable than raw Temporal workflow definitions.

### Leave
- TypeScript-only ecosystem

### Implementation
Build a thin DSL on top of Temporal:
```python
# packages/core/workflow_dsl.py
class WorkflowBuilder:
    def step(self, name, activity, *, retry=None, timeout=None): ...
    def then(self, name, activity): ...
    def parallel(self, name, activities): ...
    def branch(self, name, condition, then, else_): ...
    def loop(self, name, until): ...
    def build(self) -> type:  # returns a @workflow.defn class
        ...
```

---

# 🏗️ THE MASTER STACK (everything assembled)

```
                      ┌───────────────────────────────────┐
                      │  PRIME-SWARM-CORE                 │
                      │  (Your own orchestrator)          │
                      └───────────────────────────────────┘
                                      │
   ┌──────────────────────────────────┼─────────────────────────────────┐
   ▼                                  ▼                                 ▼
[CONTROL]                       [INTELLIGENCE]                      [DATA]
                                                                        
LangGraph: Command +            CrewAI: Role+Persona+Crew        LangChain: Document
           Checkpointer +       AutoGen: GroupChat + Reflection            + Loaders + Splitters
           Interrupt + Subgraph DSPy: Signatures + Optimizers    LlamaIndex: Hierarchical
Temporal:  Workflows (direct)   MetaGPT: SOPs per role                       retrievers
Mastra:    Fluent DSL           Smol Agents: Code-as-action     Haystack: Component
                                Swarm: Handoff primitive                  inputs/outputs
                                Agno: Composable mixins         Perplexity: Source ranking
                                                                Browser-Use: DOM-as-tree
                                                                Cursor: Diff-based edits

                          [TYPING & STRUCTURE]
                          
                          Pydantic AI: Typed tools + result validation
                          Instructor: Retry-on-validation
                          Semantic Kernel: Plugins folder convention

                          [OBSERVABILITY]
                          
                          LangSmith pattern → OTEL → Phoenix/Langfuse (OSS)
```

---

# 📦 What Your Repo Looks Like After All Heists

```
prime-swarm/
├── packages/
│   ├── core/
│   │   ├── graph/                ← LangGraph (Command, Checkpointer, Interrupt, Subgraph)
│   │   ├── workflow_dsl.py       ← Mastra-style fluent API over Temporal
│   │   ├── roles/                ← CrewAI (Role, persona library)
│   │   ├── debate/               ← AutoGen (GroupChat, Reflection)
│   │   ├── handoff.py            ← OpenAI Swarm
│   │   ├── data/
│   │   │   ├── document.py       ← LangChain Document
│   │   │   ├── loaders/          ← LangChain loaders pattern
│   │   │   └── splitters.py      ← LangChain splitters
│   │   ├── retrievers/
│   │   │   ├── base.py           ← LangChain Retriever interface
│   │   │   ├── auto_merging.py   ← LlamaIndex
│   │   │   └── hybrid.py         ← BM25 + vector
│   │   ├── prompts/
│   │   │   ├── signature.py      ← DSPy
│   │   │   └── sops/             ← MetaGPT (role-specific SOPs)
│   │   ├── tools/
│   │   │   ├── decorator.py      ← Pydantic AI @tool
│   │   │   └── ...
│   │   ├── plugins/              ← Semantic Kernel folder convention
│   │   ├── llm/
│   │   │   └── structured.py     ← Instructor retry pattern
│   │   ├── agents/
│   │   │   ├── composable.py     ← Agno mixins
│   │   │   ├── code_react.py     ← Smol Agents
│   │   │   └── reflection.py     ← AutoGen
│   │   ├── quality/
│   │   │   └── source_ranker.py  ← Perplexity/Exa heuristics
│   │   └── tracing/              ← LangSmith pattern via OTEL
│   ├── workflows/                ← Temporal (used directly)
│   ├── api/                      ← FastAPI
│   ├── cli/                      ← Typer
│   ├── multimodal/
│   │   └── browser/
│   │       └── dom_view.py       ← Browser-Use
│   ├── kg/                       ← Neo4j
│   └── observatory/
│       └── optimizers/
│           ├── bootstrap.py      ← DSPy BootstrapFewShot
│           └── mipro.py          ← DSPy MIPRO
├── tests/
└── docs/
    └── HEIST_CREDITS.md          ← acknowledge what you stole from where
```

---

# ✅ The Heist Rules (don't break these)

1. **Steal patterns, not packages.** No `langchain` in requirements.txt for orchestration. Pip-install specific small libs only if the pattern is genuinely too much work to reimplement (e.g. niche document loaders).
2. **Re-implement in your codebase style.** Don't paste their code. Write it idiomatically for your repo.
3. **Credit in docs.** `docs/HEIST_CREDITS.md` lists what came from where. Good karma, good engineering, good for hiring conversations.
4. **No abstraction without 3 use cases.** Don't build a `Component` abstraction until you have 3 components that benefit. Premature framework = your own LangChain.
5. **Test the pattern, not the framework.** Your tests cover *your* implementation. You're not validating LangChain — you've already chosen not to use it.
6. **Be willing to delete.** If a stolen pattern doesn't earn its complexity in 3 months, rip it out.

---

# 🎯 What This Buys You

| Without heisting | With heisting |
|---|---|
| Reinvent everything from scratch | Stand on giants' shoulders |
| 2× build time | Same time, 5× better ideas |
| Brittle code in places you didn't expect | Battle-tested patterns from production frameworks |
| Hire signal: "built one agent system" | Hire signal: "built one agent system, understands the entire landscape" |

---

# 🚀 Heist Priority Order

If you can't steal everything in Phase 0, do them in this order:

| Priority | Heist | Phase | Why first |
|---|---|---|---|
| **P0** | LangGraph: Command + Checkpointer + Interrupt | Phase 0 | Cleans up your existing FSM massively |
| **P0** | Pydantic AI: typed tools + @tool decorator | Phase 0 | Foundation for everything else |
| **P0** | Instructor: retry-on-validation | Phase 0 | Free reliability |
| **P0** | LangChain: Document + Loaders + Splitters | Phase 0 | You need this for data ingestion |
| **P1** | LangSmith → OTEL → Phoenix | Phase 1 | Observability before complexity |
| **P1** | Mastra: fluent workflow DSL | Phase 2 | Makes Temporal workflows readable |
| **P1** | CrewAI: Role + persona library | Phase 5 | Your debate nodes need this |
| **P1** | AutoGen: GroupChat + Reflection | Phase 5 | Debate execution model |
| **P1** | Perplexity: source ranking | Phase 0 (cheap win) | Better answers immediately |
| **P2** | DSPy: Signatures + BootstrapFewShot + MIPRO | Phase 6 | Self-learning core |
| **P2** | LlamaIndex: auto-merging retriever | Phase 4 | KG retrieval gets smarter |
| **P2** | Browser-Use: DOM tree format | Phase 3 | Browser tool reliability |
| **P3** | OpenAI Swarm: handoff primitive | Phase 5 | Specialist composition |
| **P3** | Agno: composable mixins | Phase 5 | Code organization |
| **P3** | Smol Agents: code-as-action | Phase 6 | Power-user mode |
| **P3** | MetaGPT: SOP prompts | Phase 0/6 | Prompt quality |
| **P3** | Semantic Kernel: plugins folder | Phase 0 | Organization |
| **P3** | Cursor: diff-based edits | Phase 5 | Report revision UX |

---

# 🪪 The One-Liner For Each (Memorize These)

- **LangGraph** → "state graphs with checkpointers"
- **LangChain** → "Documents + loaders + retrievers"
- **LangSmith** → "trace + dataset + evaluator format"
- **CrewAI** → "Role dataclass with goal+backstory"
- **AutoGen** → "GroupChat + Reflection"
- **DSPy** → "Signatures + Optimizers"
- **Pydantic AI** → "@tool with typed args"
- **Instructor** → "retry on validation failure"
- **Haystack** → "components with typed inputs/outputs"
- **LlamaIndex** → "auto-merging hierarchical retriever"
- **Semantic Kernel** → "plugins folder convention"
- **OpenAI Swarm** → "handoff primitive"
- **Agno** → "composable mixins"
- **Smol Agents** → "code-as-action"
- **MetaGPT** → "SOPs in role prompts"
- **Temporal** → "workflows, signals, replay" (use directly)
- **Browser-Use** → "DOM-as-tree with element IDs"
- **Perplexity** → "source whitelist + freshness ranking"
- **Cursor** → "plan-then-act + diff edits"
- **Mastra** → "fluent workflow DSL"

---

🦝 **The heist is yours. Steal smart, steal small, build big.**
