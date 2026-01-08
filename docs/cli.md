# Command-line interface

Fontshow provides a **unified command-line interface** implemented as a
dispatcher with multiple subcommands.

The supported and documented entrypoint is:

```bash
fontshow <command> [options]
```

Direct execution via `python -m` remains supported for development and
debugging purposes, but the dispatcher is the authoritative CLI.

---

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

---

## Global flags

The following flags are available on **all commands** via the dispatcher:

| Flag | Description |
|------|-------------|
| `--help` | Show usage information |
| `--version`, `-V` | Show Fontshow version |
| `--verbose`, `-v` | Enable verbose output |
| `--quiet`, `-q` | Suppress non-essential output |

Argument parsing is centralized in the dispatcher. Individual command
implementations **must not** perform their own argument parsing.

---

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

---

## Exit codes

Fontshow uses a consistent exit code contract across all commands:

| Code | Meaning |
|------|--------|
| `0` | Successful execution |
| `1` | Unrecoverable execution failure |
| `2` | CLI usage error (argument parsing) |

Warnings do **not** affect the exit code unless explicitly promoted by
command logic.

---

## Notes on `python -m` execution

Commands can also be executed directly as Python modules, for example:

```bash
python -m fontshow.preflight
python -m fontshow.dump_fonts --help
```

This execution mode:

- uses module-local argument parsing
- is supported on a best-effort basis
- may emit runtime warnings due to module re-imports
- is **not** the primary user-facing interface

All user documentation assumes the dispatcher form.

---

## Related documentation

- `decisions.md` — authoritative design and architectural decisions
- `font-inventory-schema.md` — JSON Schema reference
- `data_dictionary.md` — meaning of inventory fields
