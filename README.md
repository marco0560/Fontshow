# Fontshow


[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://marco0560.github.io/Fontshow/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Fontshow is a font inventory and catalog generation toolchain.

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

\```text
dump_fonts → parse_font_inventory → create_catalog
\```

Each stage consumes structured data produced by the previous one and
does not re-inspect font binaries unnecessarily.

---

## Installation

Fontshow is currently intended to be used from source.

\```bash
git clone https://github.com/marco0560/Fontshow.git
cd Fontshow
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
\```

---

## Usage

Typical usage follows the pipeline stages:

\```bash
python -m fontshow.dump_fonts
python -m fontshow.parse_font_inventory
python -m fontshow.create_catalog
\```

Each stage produces an explicit output artifact that can be inspected
or reused independently.

---

## Documentation

Full documentation, including architecture, data model, and API
reference, is available at:

👉 https://marco0560.github.io/Fontshow/

---

## License

Fontshow is released under the MIT License.
