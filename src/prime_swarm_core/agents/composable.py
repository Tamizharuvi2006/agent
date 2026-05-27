"""Agno-inspired composable agent wiring."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from prime_swarm_core.data.document import Document
from prime_swarm_core.retrievers.base import Retriever
from prime_swarm_core.roles.role import Role
from prime_swarm_core.tools.decorator import ToolDefinition


class Memory(Protocol):
    async def recall(self, query: str, k: int = 5) -> list[str]: ...


class Storage(Protocol):
    async def write(self, key: str, value: str) -> None: ...


@dataclass(frozen=True, slots=True)
class Agent:
    role: Role
    memory: Memory | None = None
    knowledge: Retriever | None = None
    tools: tuple[ToolDefinition, ...] = ()
    storage: Storage | None = None

    async def prepare_messages(self, user_message: str) -> list[dict[str, str]]:
        messages = [{"role": "system", "content": self.role.system_prompt()}]

        if self.memory:
            memories = await self.memory.recall(user_message)
            if memories:
                messages.append({"role": "system", "content": _format_block("Relevant memory", memories)})

        if self.knowledge:
            documents = await self.knowledge.retrieve(user_message)
            if documents:
                messages.append({"role": "system", "content": _format_documents(documents)})

        if self.tools:
            tool_names = ", ".join(tool.name for tool in self.tools)
            messages.append({"role": "system", "content": f"Available tools: {tool_names}"})

        messages.append({"role": "user", "content": user_message})
        return messages


def _format_block(title: str, items: list[str]) -> str:
    lines = [f"{index}. {item}" for index, item in enumerate(items, start=1)]
    return f"{title}:\n" + "\n".join(lines)


def _format_documents(documents: list[Document]) -> str:
    lines = []
    for index, document in enumerate(documents, start=1):
        source = document.metadata.get("source", "unknown")
        lines.append(f"{index}. source={source}\n{document.page_content}")
    return "Knowledge hits:\n" + "\n\n".join(lines)

