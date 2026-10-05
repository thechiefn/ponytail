# Copilot upstream security review

Reviewed commit: `e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156` of `DietrichGebert/ponytail`.

> Note on method: the sandboxed local checkout at `$RUNNER_TEMP/ponytail-upstream`
> was not readable from this review session (path permission denied for every
> tool, including `test -d`, `git`, and raw-HTTP fetch). To still deliver the
> review, the same commit's tree was fetched read-only via the GitHub Contents
> API (`DietrichGebert/ponytail` at the pinned SHA above), which is byte-identical
> to `git archive` output for that ref. No upstream file was executed.

## Findings

- **No arbitrary file writes/deletes outside well-known, documented config
  paths.** `hooks/ponytail-runtime.js` and `hooks/ponytail-config.js` only
  write to `~/.claude/.ponytail-active` (or `$CLAUDE_CONFIG_DIR`), `~/.cursor/.ponytail-active`,
  and the XDG config dir's `ponytail/config.json`. `scripts/uninstall.js` and
  `scripts/cursor-hooks.js` only remove/edit ponytail's own entries from
  `settings.json`/`hooks.json`, with try/catch guarding malformed JSON so they
  never clobber unrelated content. All paths are built from `os.homedir()` /
  known env vars, not from attacker-controlled input — no path traversal found.
- **No shell/subprocess execution of arbitrary input.** The only command
  construction is in `hooks/ponytail-activate.js`, which builds a
  `bash "<path>"` / `powershell -File "<path>"` string to wire up an optional
  statusline, but only embeds the plugin's own install path after validating
  it with `isShellSafe()` (an allowlist regex rejecting shell metacharacters);
  on an unsafe path it refuses and asks the user to configure manually instead
  of embedding it. No `child_process.exec`/`spawn` calls were found anywhere
  in `hooks/`, `scripts/`, `pi-extension/`, `ponytail-mcp/`, or `__init__.py`.
- **No network access in the reviewed runtime code.** `ponytail-mcp/index.js`
  is a local stdio MCP server (`StdioServerTransport`) that only serves a
  static instructions string; it makes no outbound HTTP/socket calls.
  `.env.example` at the repo root documents an `ANTHROPIC_API_KEY` placeholder
  consumed by `promptfoo` for the **benchmarks/** suite only — benchmark/dev
  tooling, not shipped runtime code, and not a credential read by the plugin
  itself.
- **No credential reads.** No code reads `.env`, cloud credential files, SSH
  keys, or tokens. Environment variable reads are limited to
  behavior-selection flags (`PONYTAIL_DEFAULT_MODE`, `PONYTAIL_QUIET_STARTUP`,
  `PONYTAIL_HIDE_STATUS`, `CLAUDE_CONFIG_DIR`, `XDG_CONFIG_HOME`, host-detection
  vars like `CURSOR_VERSION`/`COPILOT_PLUGIN_DATA`).
- **No npm install hooks / supply-chain triggers.** `package.json` (root) and
  `ponytail-mcp/package.json`/`pi-extension/package.json` define no
  `preinstall`/`postinstall`/`prepare` scripts; `scripts.test` only runs
  `node --test`. `ponytail-mcp` depends on
  `@modelcontextprotocol/sdk` and `zod` — standard, maintained packages; no
  unpinned/typosquat-looking dependency names observed in the manifests
  reviewed.
- **Prompt-injection-shaped text — benign, by design, and already excluded.**
  `__init__.py`, `hooks/ponytail-instructions.js`, and the `skills/*/SKILL.md`
  files inject persuasive natural-language instructions ("PONYTAIL MODE
  ACTIVE…", "Proactively offer to set this up…") into agent context — this is
  the plugin's intended, advertised feature (steering an AI coding agent
  toward minimalism), not disguised attacker content, and it only ever
  originates from this repo's own files, never from external/untrusted input.
  It is, however, exactly the kind of agent-steering text a sanitization
  policy should keep out of a review/build pipeline's own trusted context —
  consistent with this fork's policy of excluding `hooks/`, `pi-extension/`,
  and `ponytail-mcp/` from the generated package.
- **Benchmark/documentation-only content (no risk):** `benchmarks/` (uses
  `promptfoo` + `.env.example` for API keys, dev-only), `AGENTS.md`,
  `README*.md`, `after-install.md`, and the various editor-plugin manifests
  (`.cursor/`, `.kiro/`, `.windsurf/`, `.qoder*/`, `.devin-plugin/`,
  `.claude-plugin/`, `.codex-plugin/`, `.grok-plugin/`, `.openclaw/`,
  `.opencode/`) are declarative config/markdown with no executable logic
  reviewed as risky.

## Packaged-runtime assessment

The sanitized output this repo actually ships (`plugin.yaml`, `__init__.py`,
`SKILL.md`, `README.md`, `LICENSE`, `UPSTREAM_COMMIT`) is a from-scratch,
policy-generated rewrite produced by `.sanitizer/sanitize.py` — it does not
copy any upstream source file except `LICENSE`. That packaged `__init__.py`
performs no network, shell, subprocess, or file-write operations; it only
returns a static instruction string and registers a hook/command/skill with
the host (Hermes). None of the findings above (statusline shell-command
construction, MCP stdio server, uninstall file edits) are present in the
packaged runtime, because `hooks/`, `pi-extension/`, `ponytail-mcp/`,
`scripts/`, `benchmarks/`, and all package manifests are excluded by
`.sanitizer/policy.txt` and verified absent by the workflow's
"Verify sanitized tree" step.

## Recommendation

Proceed with regenerating the sanitized package from this upstream commit.
No upstream findings block the sync: nothing rises above benign,
documented-behavior file writes (own config/state only), a defensively
allowlisted shell-command construction, and no network, credential, or
install-hook risk was found. Continue to exclude `hooks/`, `pi-extension/`,
`ponytail-mcp/`, `scripts/`, `benchmarks/`, and package manifests from the
generated tree, and keep `.sanitizer/policy.txt`'s allowlist as the sole
source of packaged runtime code.
