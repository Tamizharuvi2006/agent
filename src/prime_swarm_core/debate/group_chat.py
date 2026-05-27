"""GroupChat-style debate loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from prime_swarm_core.roles.role import Role


@dataclass(frozen=True, slots=True)
class TranscriptMessage:
    speaker: str
    content: str


@dataclass(frozen=True, slots=True)
class DebateResult:
    topic: str
    transcript: tuple[TranscriptMessage, ...]
    summary: str


class Speaker(Protocol):
    role: Role

    async def respond(self, topic: str, transcript: tuple[TranscriptMessage, ...]) -> str: ...


@dataclass(slots=True)
class GroupChat:
    speakers: tuple[Speaker, ...]
    max_rounds: int = 4
    transcript: list[TranscriptMessage] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.speakers:
            raise ValueError("GroupChat needs at least one speaker")
        if self.max_rounds <= 0:
            raise ValueError("max_rounds must be positive")

    async def run(self, topic: str) -> DebateResult:
        for round_index in range(self.max_rounds):
            speaker = self.speakers[round_index % len(self.speakers)]
            content = await speaker.respond(topic, tuple(self.transcript))
            self.transcript.append(TranscriptMessage(speaker=speaker.role.name, content=content))
            if _consensus_marker(content):
                break
        return DebateResult(
            topic=topic,
            transcript=tuple(self.transcript),
            summary=_summarize(tuple(self.transcript)),
        )


def _consensus_marker(content: str) -> bool:
    return "[consensus]" in content.lower()


def _summarize(transcript: tuple[TranscriptMessage, ...]) -> str:
    if not transcript:
        return ""
    final = transcript[-1]
    return f"{final.speaker}: {final.content}"

