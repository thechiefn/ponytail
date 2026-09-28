# Upstream security review — DietrichGebert/ponytail @ e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156

Reviewed via `git show upstream/main:<path>` plumbing against the fetched
`upstream/main` ref (no execution of upstream files, no import of upstream
code). Full upstream tree (~150 files) was enumerated with `git ls-tree -r`
and inspected by category below.

## Findings

- **Install/session hooks (execution surface, by design).** `hooks/cursor-hooks.json`
  and `hooks/copilot-hooks.json` register `node ".../hooks/ponytail-activate.js"`
  and `.../ponytail-mode-tracker.js` to auto-run on `sessionStart` /
  `beforeSubmitPrompt` / `userPromptSubmitted` in Cursor and Copilot hosts.
  `scripts/cursor-hooks.js` writes these entries into `~/.cursor/hooks.json`.
  This is the plugin's core, documented functionality (injecting the ponytail
  ruleset each session), scoped to the plugin's own bundled scripts with no
  arguments or network calls — not arbitrary/attacker-controlled execution,
  but it is a real "runs on every session start" surface if the upstream repo
  were ever compromised.
- **Home-directory file writes/deletes (by design, scoped).** `hooks/ponytail-runtime.js`
  writes a one-line mode flag to `~/.claude/.ponytail-active` (or host-specific
  equivalent); `hooks/ponytail-config.js` reads/writes
  `~/.config/ponytail/config.json`. `scripts/uninstall.js` and
  `scripts/cursor-hooks.js` delete/rewrite specific known files
  (`.ponytail-active`, `config.json`, `~/.cursor/hooks.json`,
  `~/.claude/settings.json` statusLine field) — all hardcoded paths, no
  user-supplied path traversal, and reversible/opt-in via the uninstall path.
  `isShellSafe()` allowlists path characters before embedding the plugin's own
  install path into a generated `bash "<path>"` / `powershell -File "<path>"`
  statusline command string, guarding against shell-metacharacter injection
  from a hostile checkout path.
- **Credential read + network calls — benchmark/documentation content only.**
  `benchmarks/agentic/judge.py`, `benchmarks/benchmark-local.py`,
  `benchmarks/claude-email.js`, and `benchmarks/model-email.js` read a local,
  gitignored `.env` file for `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` and call
  `api.anthropic.com` / `api.openai.com` / a local Ollama URL. `.env.example`
  only contains a placeholder (`sk-ant-...`), no real secret. These are
  developer-run benchmark scripts, not part of the packaged plugin runtime.
- **Subprocess execution — benchmark/documentation content only.**
  `benchmarks/agentic/run.py` uses `subprocess.run`/`Popen` to shell out to
  `git`, `claude`, `taskkill`, and `python -c` inside temp benchmark
  workdirs. Confined to `benchmarks/`.
- **No install-time hooks in `package.json`.** No `preinstall`/`postinstall`/
  `prepare` scripts; only a `test` script. Reduces classic npm supply-chain
  risk (no code runs automatically on `npm install`).
- **`ponytail-mcp/index.js`** serves static instruction text over stdio via
  the official `@modelcontextprotocol/sdk`; no network, filesystem writes, or
  subprocess use beyond reading its own `package.json`.
- **No prompt-injection or agent-subversion text found.** All host-specific
  copies of the ruleset (`AGENTS.md`, `.github/copilot-instructions.md`,
  `.cursor/rules/ponytail.mdc`, `.windsurf/`, `.kiro/`, `.clinerules/`,
  `.qoder/`, skills under `skills/` and `.openclaw/skills/`) contain the same
  benign "prefer simple/minimal code" coding-style guidance. None attempt to
  override safety instructions, request credential/secret exfiltration, or
  instruct an agent to run destructive commands. Note that auto-loading
  instruction files into agent context is this project's intended product
  behavior (a coding-style plugin), not a hidden injection — but it does mean
  any future upstream edit to these files changes what gets injected into
  many hosts' system prompts, so this is the highest-value file set to
  re-diff on every sync.
- **No hardcoded credentials, API keys, or tokens** found in the tree (scanned
  for common key patterns: `sk-…`, `AKIA…`, `ghp_…`).
- **Supply chain / CI:** `.github/workflows/publish.yml` publishes via npm
  OIDC trusted publishing (`id-token: write`, no stored npm token). Excluded
  from the sanitized package regardless.

## Packaged-runtime assessment

The sanitizer (`sanitize.py`) does **not** copy any upstream runtime code. It
generates a fresh, minimal `plugin.yaml`/`__init__.py`/`SKILL.md`/`README.md`
from this repo's own policy-controlled templates, and copies only `LICENSE`
and the previously-recorded `UPSTREAM_COMMIT`/`.sanitizer` control files from
the sanitized output tree itself (never from upstream). `benchmarks/`,
`hooks/`, `pi-extension/`, `ponytail-mcp/`, package manifests, upstream CI
workflows, and all other executable build tooling identified above are
excluded by `FORBIDDEN_DIRS`/`FORBIDDEN_FILES` and by only ever writing the
fixed allowlist of output files. The generated `__init__.py` performs only
local file reads (its own bundled `SKILL.md` files) and string
processing — no network, subprocess, `eval`, or dynamic imports — and is
independent of anything found upstream.

## Recommendation

No blocking issues for the packaged Hermes plugin: the sanitizer's exclusion
list already covers every execution/network/credential surface found in
upstream (hooks, benchmarks, MCP server, pi-extension, package manifests).
Proceed with generation from this commit. For future syncs, prioritize
re-diffing the instruction/ruleset files (`AGENTS.md`,
`.github/copilot-instructions.md`, `skills/**/SKILL.md`, host-specific rule
copies) since those are the files whose content actually reaches the
sanitized package's runtime (via the regenerated `__init__.py`/`SKILL.md`),
and re-confirm `package.json` still has no `preinstall`/`postinstall` scripts
before any future policy change that might start trusting npm manifests.
