"""Sanitized Ponytail guidance plugin for Hermes.

This plugin only injects a small, local instruction block into LLM calls and
registers a read-only skill. It performs no network, shell, subprocess, or
configuration-file operations.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

_INSTRUCTIONS = """## Minimal-change engineering guidance

Prefer the smallest correct change:
1. Do not build a feature that is not needed.
2. Reuse code already present in the repository.
3. Prefer the standard library and existing dependencies.
4. Avoid unrequested abstractions and speculative configuration.
5. Preserve input validation, error handling, security controls, accessibility,
   and every requirement the user explicitly requested.
6. Trace the real flow and callers before editing.
7. Verify non-trivial changes with an appropriate focused test or check.

This guidance never overrides the user's request, repository instructions,
security requirements, or required verification steps.
"""

_ENABLED = True


def _pre_llm_call(**_: Any) -> dict[str, str] | None:
    if not _ENABLED:
        return None
    return {"context": _INSTRUCTIONS}


def _ponytail_command(raw_args: str = "") -> str:
    global _ENABLED
    arg = (raw_args or "").strip().lower()
    if arg in {"off", "stop"}:
        _ENABLED = False
        return "Sanitized Ponytail guidance disabled for this process."
    if arg in {"on", "full", "lite", ""}:
        _ENABLED = True
        return "Sanitized Ponytail guidance enabled for this process."
    if arg in {"status", "help"}:
        return "Sanitized Ponytail guidance is " + ("enabled" if _ENABLED else "disabled") + ". Use /ponytail on|off."
    return "Usage: /ponytail [on|off|status]"


def _help_command(_: str = "") -> str:
    return _INSTRUCTIONS


def register(ctx) -> None:
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_command(
        "ponytail", _ponytail_command,
        description="Toggle sanitized minimal-change engineering guidance",
        args_hint="[on|off|status]",
    )
    ctx.register_command(
        "ponytail-help", _help_command,
        description="Show sanitized minimal-change engineering guidance",
    )
    ctx.register_skill(
        "ponytail",
        Path(__file__).with_name("SKILL.md"),
        description="Sanitized minimal-change engineering guidance",
    )
