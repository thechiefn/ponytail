"""Build a small, reviewed Hermes plugin from an upstream Ponytail checkout.

The source tree is treated as untrusted data. This script never imports or
executes source files from it and copies only the upstream license. Runtime
code and instructions are generated from this repository's policy.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

PLUGIN_YAML = """name: ponytail-sanitized
version: \"4.10.0-sanitized\"
description: \"Sanitized Ponytail-style minimalism guidance for Hermes Agent; local context injection only.\"
author: \"Joe Crandall (sanitized from DietrichGebert/ponytail)\"
provides_hooks:
  - pre_llm_call
provides_commands:
  - ponytail
  - ponytail-help
provides_skills:
  - ponytail
"""

PLUGIN_PY = """\"\"\"Sanitized Ponytail guidance plugin for Hermes.

This plugin only injects a small, local instruction block into LLM calls and
registers a read-only skill. It performs no network, shell, subprocess, or
configuration-file operations.
\"\"\"
from __future__ import annotations

from pathlib import Path
from typing import Any

_INSTRUCTIONS = \"\"\"## Minimal-change engineering guidance

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
\"\"\"

_ENABLED = True


def _pre_llm_call(**_: Any) -> dict[str, str] | None:
    if not _ENABLED:
        return None
    return {\"context\": _INSTRUCTIONS}


def _ponytail_command(raw_args: str = \"\") -> str:
    global _ENABLED
    arg = (raw_args or \"\").strip().lower()
    if arg in {\"off\", \"stop\"}:
        _ENABLED = False
        return \"Sanitized Ponytail guidance disabled for this process.\"
    if arg in {\"on\", \"full\", \"lite\", \"\"}:
        _ENABLED = True
        return \"Sanitized Ponytail guidance enabled for this process.\"
    if arg in {\"status\", \"help\"}:
        return \"Sanitized Ponytail guidance is \" + (\"enabled\" if _ENABLED else \"disabled\") + \". Use /ponytail on|off.\"
    return \"Usage: /ponytail [on|off|status]\"


def _help_command(_: str = \"\") -> str:
    return _INSTRUCTIONS


def register(ctx) -> None:
    ctx.register_hook(\"pre_llm_call\", _pre_llm_call)
    ctx.register_command(
        \"ponytail\", _ponytail_command,
        description=\"Toggle sanitized minimal-change engineering guidance\",
        args_hint=\"[on|off|status]\",
    )
    ctx.register_command(
        \"ponytail-help\", _help_command,
        description=\"Show sanitized minimal-change engineering guidance\",
    )
    ctx.register_skill(
        \"ponytail\",
        Path(__file__).with_name(\"SKILL.md\"),
        description=\"Sanitized minimal-change engineering guidance\",
    )
"""

SKILL_MD = """---
name: ponytail
version: \"4.10.0-sanitized\"
description: Sanitized minimal-change engineering guidance.
---

Prefer the smallest correct change. Reuse existing code, prefer the standard library and installed dependencies, and avoid unrequested abstractions. Do not simplify away input validation, security controls, error handling, accessibility, or explicit requirements. Trace the real flow before editing and run a focused verification for non-trivial changes. This guidance never overrides user requests, repository instructions, or required safety checks.
"""

README_MD = """# Ponytail sanitized fork

This repository is a generated, sanitized derivative of
[DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail).

The committed workflow fetches upstream as untrusted input, asks GitHub Copilot
CLI for a bounded review, and regenerates this small native Hermes plugin from
policy-controlled files. It intentionally excludes upstream benchmarks,
third-party host hooks, MCP/network code, CI workflows, and shell execution.

The upstream commit used for the current generated tree is recorded in
`UPSTREAM_COMMIT`.

## Local use

Copy this directory into the Hermes plugin directory or use the generated
plugin files with Hermes. The plugin provides `/ponytail [on|off|status]` and
`/ponytail-help`.

Do not execute files from the upstream source tree as part of the sanitization
process.
"""

FORBIDDEN_DIRS = {"benchmarks", ".github", ".git", "hooks", "pi-extension", "ponytail-mcp"}
FORBIDDEN_FILES = {"package.json", "package-lock.json", "npm-shrinkwrap.json"}


def _read_controls(output: Path) -> dict[str, bytes]:
    controls: dict[str, bytes] = {}
    for rel in (Path(".sanitizer/sanitize.py"), Path(".sanitizer/policy.txt"), Path(".sanitizer/COPILOT-REVIEW.md"), Path(".sanitizer/UPSTREAM_COMMIT"), Path(".github/workflows/sanitize-upstream.yml")):
        path = output / rel
        if path.is_file():
            controls[str(rel)] = path.read_bytes()
    return controls


def _clean_output(output: Path) -> None:
    for child in output.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def sanitize(source: Path, output: Path) -> None:
    source = source.resolve()
    output = output.resolve()
    if not source.is_dir() or source == output:
        raise ValueError("source must be a separate directory")
    license_path = source / "LICENSE"
    if not license_path.is_file():
        raise FileNotFoundError("upstream LICENSE is required")

    controls = _read_controls(output)
    _clean_output(output)

    (output / ".github/workflows").mkdir(parents=True, exist_ok=True)
    (output / ".sanitizer").mkdir(parents=True, exist_ok=True)
    (output / "plugin.yaml").write_text(PLUGIN_YAML, encoding="utf-8")
    (output / "__init__.py").write_text(PLUGIN_PY, encoding="utf-8")
    (output / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
    (output / "README.md").write_text(README_MD, encoding="utf-8")
    shutil.copy2(license_path, output / "LICENSE")
    (output / "UPSTREAM_COMMIT").write_bytes(
        controls.get(".sanitizer/UPSTREAM_COMMIT", b"unknown\n")
    )
    for rel, data in controls.items():
        path = output / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    (output / ".sanitizer/policy.txt").write_text(
        "Generated allowlist: plugin.yaml, __init__.py, SKILL.md, README.md, LICENSE, UPSTREAM_COMMIT, and sanitizer controls only.\n"
        "Excluded: benchmarks, hooks, pi-extension, ponytail-mcp, package manifests, upstream CI, and executable build tooling.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sanitize(args.source, args.output)


if __name__ == "__main__":
    main()
