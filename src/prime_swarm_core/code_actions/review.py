"""Smolagents-inspired code-as-action review gate.

This module does not execute LLM-generated code. It only performs a conservative
review so a future sandbox can decide whether to allow execution.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field


DEFAULT_BLOCKED_NAMES = {
    "exec",
    "eval",
    "compile",
    "__import__",
    "open",
    "input",
}
DEFAULT_BLOCKED_MODULES = {
    "os",
    "subprocess",
    "socket",
    "shutil",
    "pathlib",
    "sys",
}


@dataclass(frozen=True, slots=True)
class CodeActionPolicy:
    enabled: bool = False
    blocked_names: frozenset[str] = field(default_factory=lambda: frozenset(DEFAULT_BLOCKED_NAMES))
    blocked_modules: frozenset[str] = field(default_factory=lambda: frozenset(DEFAULT_BLOCKED_MODULES))


@dataclass(frozen=True, slots=True)
class CodeActionReview:
    allowed: bool
    reasons: tuple[str, ...]


def review_code_action(code: str, policy: CodeActionPolicy | None = None) -> CodeActionReview:
    policy = policy or CodeActionPolicy()
    reasons: list[str] = []

    if not policy.enabled:
        reasons.append("code-as-action is disabled")

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        reasons.append(f"syntax error: {exc.msg}")
        return CodeActionReview(allowed=False, reasons=tuple(reasons))

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in policy.blocked_names:
            reasons.append(f"blocked call: {node.func.id}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in policy.blocked_modules:
                    reasons.append(f"blocked import: {root}")
        if isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".", 1)[0]
            if root in policy.blocked_modules:
                reasons.append(f"blocked import: {root}")

    return CodeActionReview(allowed=not reasons, reasons=tuple(reasons))

