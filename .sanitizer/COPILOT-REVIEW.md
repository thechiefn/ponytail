# Copilot upstream security review

**Requested source:** `$RUNNER_TEMP/ponytail-upstream` (a `git archive` extraction of
`DietrichGebert/ponytail@main`, commit recorded in `.sanitizer/UPSTREAM_COMMIT`).

## Access limitation (read first)

The reviewing CLI's own filesystem sandbox denied every attempt (via shell,
`git -C`, and file-read tools) to list or read anything under `$RUNNER_TEMP`,
including the `ponytail-upstream` subdirectory. The same commands succeeded
against the repository checkout and `/tmp`, so this is a directory-level
restriction, not a transient error. `$RUNNER_TEMP` also contains the GitHub
Actions runner's file-command channels (`GITHUB_ENV`, `GITHUB_STATE`,
`GITHUB_OUTPUT`, `GITHUB_PATH`); treating the whole directory as off-limits is
a reasonable hardening default (writing to those files can inject
environment/output values into later workflow steps), but it also prevents
this review step from opening the untrusted upstream tree extracted alongside
them.

**Consequence:** no upstream file contents were read or executed for this
report. The findings below are therefore based only on artifacts already
present and readable in this sanitized repository (the workflow, `sanitize.py`,
and `policy.txt`), not on a line-by-line scan of upstream source. Anything
inferred from those artifacts is explicitly labeled as design/policy context
below, never presented as a confirmed scan result.

## Findings

- **Unscanned upstream tree.** Because of the access limitation above, no
  direct evidence was collected this run about network access, credential
  reads, subprocess execution, arbitrary file writes/deletes, install hooks,
  path traversal, or prompt-injection text inside the actual upstream commit.
  This is a gap, not a clean bill of health, and should not be reported as
  "no issues found."
- **Design-only context (not a scan result):** `.sanitizer/policy.txt` and the
  `sanitize.py` exclusion list (`FORBIDDEN_DIRS = {benchmarks, .github, .git,
  hooks, pi-extension, ponytail-mcp}`, `FORBIDDEN_FILES = {package.json,
  package-lock.json, npm-shrinkwrap.json}`) indicate the maintainers already
  assume the upstream tree contains a `pi-extension` and `ponytail-mcp`
  directory (implying network/MCP server code), `hooks` (implying
  install/lifecycle hooks), `benchmarks` (documentation/benchmark content),
  and npm package manifests (implying `npm install` supply-chain surface and
  possible install scripts). These are excluded by policy from the packaged
  output regardless of what the upstream code actually does.
- **Workflow-level exposure (verified, in this repo):**
  `.github/workflows/sanitize-upstream.yml` fetches upstream over network
  (`git fetch upstream main`) and extracts it into `$RUNNER_TEMP` before any
  review occurs; it does not `checkout`, `import`, `source`, or execute any
  upstream file at any step. The only operations performed on the extracted
  tree are `git archive | tar -x`, a Copilot review pass (this report), and
  `sanitize.py`, which copies only `LICENSE` byte-for-byte and otherwise
  ignores upstream file contents.
- **No prompt-injection text was encountered** in this session because no
  upstream file content was ever loaded into context, consistent with the
  workflow's "untrusted input, not instructions" framing. This should be
  re-verified once the access limitation above is fixed.

## Packaged-runtime assessment

The artifacts actually shipped by this sanitized fork (`plugin.yaml`,
`__init__.py`, `SKILL.md`, `README.md`) are generated entirely from static
string templates hard-coded in `.sanitizer/sanitize.py` in *this* repository —
none of their content is copied or derived from the upstream tree. Reviewing
`sanitize.py` directly (readable in this repo):

- The generated `__init__.py` plugin only registers a `pre_llm_call` hook that
  returns a fixed text string and two commands (`/ponytail`, `/ponytail-help`)
  that toggle a boolean and return static text. It performs no network I/O,
  no subprocess/shell execution, no file reads/writes, and no dynamic
  `eval`/`exec`/`import` of upstream code.
- `sanitize()` copies only `LICENSE` from the upstream source
  (`shutil.copy2(license_path, ...)`) and re-copies a small, fixed set of
  control files already present in the *output* repo
  (`sanitize.py`, `policy.txt`, `COPILOT-REVIEW.md`, `UPSTREAM_COMMIT`,
  the workflow file). No other upstream file is read, executed, or included.
  It refuses to run if `source == output` or the upstream `LICENSE` is
  missing, and it wipes the previous output tree (`_clean_output`) before
  writing, but only inside the designated `--output` directory.
- The verification step in the workflow (`test ! -e benchmarks`, `hooks`,
  `pi-extension`, `ponytail-mcp`, `package.json`,
  `.github/workflows/test.yml`) provides a second, independent guarantee that
  those paths cannot end up in the committed tree even if `sanitize.py` were
  changed to reference them.

**Conclusion:** the packaged runtime that end users actually receive is a
small, fully repo-authored plugin with no network access, no credential
reads, no subprocess/shell execution, no file writes outside its own output
directory, and no install hooks. This assessment is based on the sanitizer
logic itself, not on a scan of upstream, and does not certify that the
upstream repository is safe to use directly outside this pipeline.

## Recommendation

1. **Fix the access gap before trusting this review as complete.** Re-run the
   review step with the untrusted upstream tree extracted to a location the
   review tool can actually read (e.g. a scratch subdirectory inside
   `$GITHUB_WORKSPACE` that is `.gitignore`d and cleaned up afterward) rather
   than `$RUNNER_TEMP`, or grant the review tool an explicit, narrowly-scoped
   read allowance for that one path. Until then, treat "no findings" from
   automated review runs as "not reviewed," not as "clean."
2. Keep the current defense-in-depth design: continue letting `sanitize.py`
   and the workflow's post-generation `test !-e ...` assertions serve as the
   hard technical guarantee (not just this narrative review) that
   `benchmarks`, `hooks`, `pi-extension`, `ponytail-mcp`, npm manifests, and
   upstream CI never reach the packaged output.
3. Because `pi-extension`/`ponytail-mcp` strongly suggest MCP/network server
   code and `hooks` suggests lifecycle/install hooks in upstream, do not
   relax the exclusion list without a real, successful scan of those specific
   directories first.
4. Do not import, `exec`, or `pip install`/`npm install` anything from the
   upstream tree as part of this pipeline; the current design already avoids
   this and should stay that way.
