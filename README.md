# Fontshow

[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://marco0560.github.io/Fontshow/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://github.com/marco0560/fontshow/actions/workflows/ci.yml/badge.svg)](https://github.com/marco0560/fontshow/actions/workflows/ci.yml)

## What is Fontshow

Fontshow is a command-line toolkit for **font discovery, analysis, validation,
and catalog generation**.

It provides a structured pipeline to:

- inspect the local font environment
- extract a raw inventory of installed fonts
- enrich the inventory with Unicode, script, and language metadata
- validate the resulting data against a formal schema
- generate human-readable artifacts (e.g. PDF catalogs)

Fontshow is designed to be:

- reproducible
- testable
- schema-driven
- explicit about its execution model and return codes

## Quick start

Fontshow exposes a unified command-line interface through a dispatcher.

The recommended entrypoint is:

```bash
fontshow <command> [options]
```

A typical end-to-end workflow is:

```bash
fontshow preflight
fontshow dump-fonts
fontshow parse-inventory
fontshow create-catalog
```

Each step consumes the output of the previous one and produces a well-defined
artifact for the next stage.

## Features

- Cross-platform font discovery (Linux and Windows)
- Deep font metadata extraction using fontTools
- Script and language inference based on Unicode coverage
- Structured JSON font inventory
- LaTeX catalog generation (XeLaTeX / LuaLaTeX)
- Reproducible, inventory-driven workflow

## CLI design notes

Fontshow commands follow a strict execution contract:

```python
def main(args) -> int
```

- Argument parsing is handled by the dispatcher
- Command logic never calls `sys.exit()`
- Each command returns an explicit exit code
- The dispatcher is responsible for process termination

This guarantees consistent behavior across all commands and simplifies
testing and automation.

For a detailed rationale, see `decisions.md`.

## Notes on direct module execution

Commands can also be executed directly via Python, for example:

```bash
python -m fontshow.dump_fonts --help
```

This mode is supported primarily for development and debugging.

The unified dispatcher (`fontshow <command>`) is the authoritative and
documented user interface.

## Pipeline overview

```text
dump_fonts → parse_font_inventory → create_catalog
```

Each stage consumes structured data produced by the previous one and
does not re-inspect font binaries unnecessarily.

---
<!-- cheatsheet:start -->

## Installation

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/marco0560/Fontshow.git
cd Fontshow
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

This installs Fontshow in editable mode using the project’s
`pyproject.toml` configuration.

<!-- cheatsheet:end -->

<!-- cheatsheet:start -->

## Repository cleanup utility

The repository includes a helper script to remove generated artifacts and
temporary files while keeping the working tree clean:

```bash
python scripts/clean_repo.py
```
<!-- cheatsheet:end -->

The script removes **only files ignored by Git** (according to `.gitignore`)
and never deletes tracked files.

A dry-run mode is available to safely preview the cleanup:

<!-- cheatsheet:start -->
```bash
python scripts/clean_repo.py --dry-run
```
<!-- cheatsheet:end -->

### Safety guarantees

Some paths are explicitly protected and will **never be removed**, even if
ignored by Git. In particular:

- `.venv` (Python virtual environment)

This ensures that the cleanup process is safe to run during development
without risking the local working environment.

---
<!-- cheatsheet:start -->

## Available commands

| Command                    | Description                                 |
|----------------------------|---------------------------------------------|
| `fontshow preflight`       | Run environment and dependency checks       |
| `fontshow dump-fonts`      | Extract a raw font inventory                |
| `fontshow parse-inventory` | Enrich and validate a font inventory        |
| `fontshow create-catalog`  | Generate output artifacts from an inventory |

Use `--help` on any command to see available options:

```bash
fontshow dump-fonts --help
```
<!-- cheatsheet:end -->

Direct execution of files such as:

```bash
python fontshow/dump_fonts.py
```

is not supported and may produce inconsistent behavior.

Use the unified dispatcher instead:

```bash
fontshow dump-fonts --help
fontshow parse-inventory --help
fontshow create-catalog --help
```

Direct module execution via `python -m` is supported primarily for development
and debugging:

```bash
python -m fontshow.dump_fonts --help
python -m fontshow.parse_font_inventory --help
python -m fontshow.create_catalog --help
```

The authoritative, user-facing interface is always `fontshow <command>`.

---

<!-- cheatsheet:start -->

## Available tools

### Dump system fonts

Generate a JSON inventory of installed fonts:

```bash
python -m fontshow.dump_fonts \
  --output font_inventory.json
```
<!-- cheatsheet:end -->

This command produces a versioned inventory including:

- font metadata
- coverage information
- environment and system context

---

<!-- cheatsheet:start -->
### Parse and normalize inventory

Normalize and enrich a previously generated inventory:

```bash
python -m fontshow.parse_font_inventory \
  --output font_inventory_enriched.json
```
<!-- cheatsheet:end -->

<!-- cheatsheet:start -->
An optional soft validation of the inventory structure can be performed with:

```bash
python -m fontshow.parse_font_inventory \
  --validate-inventory
```
<!-- cheatsheet:end -->

---

<!-- cheatsheet:start -->
### Generate LaTeX catalog

Generate a LaTeX catalog from a parsed inventory:

```bash
python -m fontshow.create_catalog
```
<!-- cheatsheet:end -->

Additional options are available for:

- test font selection
- debug output
- LaTeX generation control

See:

```bash
fontshow create-catalog --help
```

---

## Versioning

Fontshow follows semantic versioning:

- **MAJOR**: breaking changes
- **MINOR**: new features, backward-compatible
- **PATCH**: bug fixes

The current version is exposed via:

```python
fontshow.__version__
```

Each generated inventory records:

- the schema version
- the tool version
- the execution environment

---

## Documentation

- `cli.md` — command-line interface reference
- `decisions.md` — architectural and design decisions
- `font-inventory-schema.md` — JSON Schema for inventories
- `data_dictionary.md` — meaning of inventory fields

The documentation is intentionally split between **what the tool does**
and **why it is designed this way**.

## License

Fontshow is released under the MIT License.
