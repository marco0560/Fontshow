# Fontshow


[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://marco0560.github.io/Fontshow/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Fontshow is a Python-based toolchain for inspecting system fonts and generating
LaTeX font catalogs in a reproducible and debuggable way.

The project is structured as a **proper Python package** and is intended to be
executed using Python’s module execution mechanism.

It discovers installed fonts, extracts low-level metadata, performs
script and language inference, and generates printable LaTeX catalogs.

The project is designed as a linear, data-driven pipeline with explicit
data contracts between stages.

---

## Features

- Cross-platform font discovery (Linux and Windows)
- Deep font metadata extraction using fontTools
- Script and language inference based on Unicode coverage
- Structured JSON font inventory
- LaTeX catalog generation (XeLaTeX / LuaLaTeX)
- Reproducible, inventory-driven workflow

---

## Pipeline overview

```text
dump_fonts → parse_font_inventory → create_catalog
```

Each stage consumes structured data produced by the previous one and
does not re-inspect font binaries unnecessarily.

---

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/marco0560/Fontshow.git
cd Fontshow
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Execution model (important)

Fontshow is a Python package named `fontshow`.

All tools **must be executed as modules**, using the `-m` flag:

```bash
python -m fontshow.<tool>
```

Direct execution of files such as:

```bash
python fontshow/dump_fonts.py
```

is **not supported** and will result in import errors.

---

## Available tools

### Dump system fonts

Generate a JSON inventory of installed fonts:

```bash
python -m fontshow.dump_fonts \
  --output font_inventory.json
```

This command produces a versioned inventory including:

- font metadata
- coverage information
- environment and system context

---

### Parse and normalize inventory

Normalize and enrich a previously generated inventory:

```bash
python -m fontshow.parse_font_inventory \
  font_inventory.json \
  --output font_inventory_enriched.json
```

An optional soft validation of the inventory structure can be performed with:

```bash
python -m fontshow.parse_font_inventory \
  font_inventory.json \
  --validate-inventory
```

---

### Generate LaTeX catalog

Generate a LaTeX catalog from a parsed inventory:

```bash
python -m fontshow.create_catalog \
  font_inventory_enriched.json
```

Additional options are available for:

- test font selection
- debug output
- LaTeX generation control

See:

```bash
python -m fontshow.create_catalog --help
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

Project documentation is available at:

👉 https://marco0560.github.io/Fontshow/

It includes:

- architecture overview
- data dictionary
- testing procedures
- example inventories

---

## License

Fontshow is released under the MIT License.
