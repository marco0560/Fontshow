# Preflight

The `preflight` command performs **environment and dependency checks**
required by the Fontshow pipeline.

It is intended as the first step in any workflow.

---

## Purpose

Preflight verifies that:

- the execution environment is supported
- required external tools are available
- optional capabilities (e.g. LaTeX) are detected
- known incompatibilities are reported early

No files are created or modified.

---

## Invocation

<!-- cheatsheet:start -->
```bash
fontshow preflight
```
<!-- cheatsheet:end -->

---

## Options

The preflight command supports the standard global flags:

| Flag | Description |
| ------ | ------------- |
| `-v`, `--verbose` | Show detailed check results |
| `-q`, `--quiet` | Suppress all output |
| `-V`, `--version` | Show Fontshow version |
| `--help` | Show usage information |

---

## Output

By default, preflight prints a short summary:

```text
Preflight passed.
```

With `--verbose`, individual checks are shown:

```text
[ OK ] environment.support: Running on supported Linux bare-metal environment
[ OK ] font_discovery.capability: fontconfig available
[ OK ] latex.capability: LuaLaTeX available
Preflight passed.
```

When `--quiet` is specified, no output is produced.

---

## Exit codes

<!-- cheatsheet:start -->
| Code | Meaning |
| ------ | -------- |
| `0` | All required checks passed |
| `1` | One or more blocking checks failed |
<!-- cheatsheet:end -->

Warnings do not affect the exit code unless explicitly promoted.

---

## Notes

- Preflight does **not** inspect fonts or inventories
- Results are not persisted
- The command is safe to run repeatedly

For the design rationale and execution model, see `decisions.md`.
