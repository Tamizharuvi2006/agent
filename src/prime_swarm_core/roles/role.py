"""Agent role definition."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


ROLE_TEMPLATE = """You are {name}.

Goal: {goal}

Backstory: {backstory}

Allowed tools: {allowed_tools}
Expected output: {expected_output}
"""


@dataclass(frozen=True, slots=True)
class Role:
    name: str
    goal: str
    backstory: str
    allowed_tools: tuple[str, ...] = ()
    model: str = "default"
    temperature: float = 0.3
    max_iterations: int = 8
    expected_output: str = "A concise, useful answer."
    sop: tuple[str, ...] = field(default_factory=tuple)

    def system_prompt(self) -> str:
        prompt = ROLE_TEMPLATE.format(
            **{
                **asdict(self),
                "allowed_tools": ", ".join(self.allowed_tools) or "none",
            }
        ).strip()
        if self.sop:
            steps = "\n".join(f"{index}. {step}" for index, step in enumerate(self.sop, start=1))
            prompt = f"{prompt}\n\nStandard operating procedure:\n{steps}"
        return prompt

