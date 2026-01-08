# Getting started

This page provides a minimal introduction to installing and running
Fontshow end-to-end.

---

## Installation

Fontshow can be installed via pip.

### Standard installation

```bash
pip install fontshow
```

### Editable / development installation

For contributors or local development:

```bash
git clone https://github.com/marco0560/Fontshow.git
cd Fontshow
pip install -e .
```

---

## Quick pipeline

A typical workflow consists of four steps:

```bash
fontshow preflight
fontshow dump-fonts
fontshow parse-inventory
fontshow create-catalog
```

Each step consumes the output of the previous one and produces a
well-defined artifact.

---

## Output files

By default:

- `dump-fonts` produces a **raw inventory** JSON file
- `parse-inventory` produces an **enriched inventory** JSON file
- `create-catalog` produces **output artifacts** (e.g. PDF catalog)

Output file names and locations can be customized via command options.
Use `--help` on each command for details.

---

## LaTeX requirements

Catalog generation relies on LaTeX.

Notes:

- A full TeX distribution (e.g. TeX Live) is recommended
- `lualatex` must be available in the execution environment
- Compilation must occur on the same system where fonts were discovered,
  so that font paths remain valid

If LaTeX is missing, preflight will report the limitation and
catalog generation may fail.

---

## Next steps

- See `cli.md` for a complete CLI overview
- See `pipeline.md` for a detailed explanation of each stage
- See `tools/` pages for command-specific documentation
