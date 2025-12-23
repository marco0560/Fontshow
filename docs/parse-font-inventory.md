# parse_font_inventory.py

This document describes `parse_font_inventory.py`, the second stage of the
Fontshow pipeline.

The script parses the canonical `font_inventory.json` produced by
`dump_fonts.py` and enriches it with **deterministic inference** of scripts and
languages.

---------------------------------------------------------------------

## Purpose

- Compensate for missing metadata (especially on Windows).
- Keep the pipeline OS-agnostic after the dump phase.
- Prepare a stable, enriched structure for `create_catalog.py`.

Important:
- No font files are accessed.
- Only the JSON inventory is processed.
- Declared metadata is never overwritten.

---------------------------------------------------------------------

## Position in the pipeline

dump_fonts.py
  → font_inventory.json
parse_font_inventory.py
  → font_inventory_enriched.json
create_catalog.py
  → LaTeX catalog

This separation ensures that:
- OS-specific logic is isolated in the dump phase.
- Inference rules can evolve independently.
- Rendering code remains simple.

---------------------------------------------------------------------

## Inference model

Inference is **best-effort**, deterministic, and explicitly marked in the output.

The goal is not to certify language support, but to:
- infer supported scripts,
- select plausible example languages,
- drive catalog rendering decisions.

---------------------------------------------------------------------

## Inference levels

The aggressiveness of inference can be selected from the command line.

Levels:

- conservative
  Very strict inference. Minimizes false positives.

- medium (default)
  Balanced behavior. Recommended for Fontshow.

- aggressive
  Exploratory mode. Higher recall, higher risk of false positives.

The selected level is recorded in the output metadata.

---------------------------------------------------------------------

## Script inference

Scripts are inferred from Unicode coverage using predefined ranges.

Supported scripts:

- Latin
- Greek
- Cyrillic
- Arabic
- Hebrew
- Devanagari
- Armenian
- Japanese
- Vietnamese
- Coptic
- Ethiopic (Tigrinya)
- Han
- Hangul
- Thai

The minimum amount of evidence required depends on the inference level.

---------------------------------------------------------------------

## Language inference

Languages are inferred *from scripts*, not directly from the font.

Key principles:
- Languages are examples, not guarantees.
- Multiple candidate languages may be listed.
- Downstream tools should usually pick the first one.

Example:
- Script: latn → languages: en, it, fr, de, es, vi
- Script: jpan → language: ja
- Script: ethi → language: ti

---------------------------------------------------------------------

## Output structure

Each font entry gains an additional `inference` block.

Example:

{
  "inference": {
    "level": "medium",
    "scripts": ["latn"],
    "languages": ["it", "fr"],
    "declared_scripts": [],
    "declared_languages": []
  }
}

Declared metadata (from FontConfig on Linux) is preserved for comparison.

---------------------------------------------------------------------

## Usage

Basic usage:

python3 scripts/parse_font_inventory.py font_inventory.json

Custom inference level:

python3 scripts/parse_font_inventory.py font_inventory.json \
  --infer-level aggressive \
  --output font_inventory_enriched.json

---------------------------------------------------------------------

## Design notes

- Inference rules are deterministic and auditable.
- No external tools (FontForge, ExifTool) are required.
- The script is fully cross-platform.
- The design favors long-term maintainability over clever heuristics.
