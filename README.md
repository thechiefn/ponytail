# Ponytail sanitized fork

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
