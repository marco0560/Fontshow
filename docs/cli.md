# Command-line interface

Fontshow provides a **unified command-line interface** implemented as a
dispatcher with multiple subcommands.

The supported and documented entrypoint is:

```bash
fontshow <command> [options]
```

Direct execution via `python -m` remains supported for development and
debugging purposes, but the dispatcher is the authoritative CLI.

## Available commands

```text
fontshow preflight
fontshow dump-fonts
fontshow parse-inventory
fontshow create-catalog
```

Typical pipeline:

```bash
fontshow preflight
fontshow dump-fonts
fontshow parse-inventory
fontshow create-catalog
```

## Global flags

The following flags are available on **all commands** via the dispatcher:

| Flag | Description |
| ------ | ------------- |
| `--help` | Show usage information |
| `--version`, `-V` | Show Fontshow version |
| `--verbose`, `-v` | Enable verbose output |
| `--quiet`, `-q` | Suppress non-essential output |

Argument parsing is centralized in the dispatcher. Individual command
implementations **must not** perform their own argument parsing.

## Execution model

Each CLI command exposes a callable with the following contract:

```python
def main(args) -> int
```

Rules:

- `main(args)` contains **only command logic**
- It **returns** an integer exit code
- It **must not** call `sys.exit()`
- Argument parsing is handled by the dispatcher

This guarantees identical behavior across all supported entrypoints.

## Exit codes

Fontshow uses a consistent exit code contract across all commands:

| Code | Meaning |
| ------ | -------- |
| `0` | Successful execution |
| `1` | Unrecoverable execution failure |
| `2` | CLI usage error (argument parsing) |

Warnings do **not** affect the exit code unless explicitly promoted by
command logic.

## Preflight command behavior

The `fontshow preflight` command performs a series of environment and
dependency checks and reports their outcome to the user.

### Output semantics

Preflight checks may emit **warnings** and **errors**, which are classified
by severity:

- **Warnings** indicate suboptimal or incomplete environments
- **Errors** indicate missing capabilities that may affect downstream steps

Example output:

```text
[WARN] environment.support: Running on linux in a ci environment
[ERROR] latex.capability: LuaLaTeX not available
Preflight failed.
```

### Exit codes for preflight

The exit code of `fontshow preflight` follows these rules:

- Exit code **0**
  - No checks reported `ERROR`
- Exit code **1**
  - One or more checks reported `ERROR`

Warnings alone never cause a non-zero exit code.

### CI environments

In Continuous Integration (CI) environments, some capabilities
(e.g. LaTeX toolchains) are intentionally unavailable.

In such cases:

- Related checks may emit `ERROR` diagnostics
- The command may still be considered successful if the CI policy
  downgrades those errors
- Tests explicitly mock and control preflight results

This design allows `fontshow preflight` to remain informative without
forcing CI environments to fully replicate production setups.

### Quiet mode

When invoked with `--quiet`, the command:

- Suppresses all standard output
- Preserves the exit code semantics described above

Example:

```bash
fontshow preflight --quiet
```

This mode is intended for scripting and CI usage.

## Notes on `python -m` execution

Commands can also be executed directly as Python modules, for example:

```bash
python -m fontshow.preflight
python -m fontshow.cli.dump_fonts --help
```

This execution mode:

- uses module-local argument parsing
- is supported on a best-effort basis
- may emit runtime warnings due to module re-imports
- is **not** the primary user-facing interface

All user documentation assumes the dispatcher form.

## Related documentation

- `decisions.md` — authoritative design and architectural decisions
- Inventory schema documentation: `docs/schema/index.md`
- `data_dictionary.md` — meaning of inventory fields
