"""MetaGPT-inspired SOP templates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SOPTemplate:
    name: str
    steps: tuple[str, ...]
    output_template: str

    def render(self) -> str:
        return render_sop(self.steps, self.output_template)


def render_sop(steps: tuple[str, ...] | list[str], output_template: str) -> str:
    if not steps:
        raise ValueError("SOP needs at least one step")
    numbered_steps = "\n".join(f"{index}. {step}" for index, step in enumerate(steps, start=1))
    return f"Standard operating procedure:\n{numbered_steps}\n\nOutput template:\n{output_template.strip()}"

