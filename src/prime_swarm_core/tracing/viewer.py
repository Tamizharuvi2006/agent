"""Tiny JSONL trace viewer."""

from __future__ import annotations

import json
from pathlib import Path
import sys


def render_trace_tree(path: str | Path) -> str:
    spans = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    lines: list[str] = []
    for span in spans:
        attrs = span.get("attributes", {})
        node = attrs.get("metadata", {}).get("node", "")
        suffix = f" [{node}]" if node else ""
        lines.append(f"- {span['name']}{suffix}")
        outputs = attrs.get("outputs") or {}
        if outputs:
            lines.append(f"  outputs: {outputs}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    if len(args) != 1:
        print("usage: python -m prime_swarm_core.tracing.viewer TRACE.jsonl")
        return 2
    print(render_trace_tree(args[0]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
