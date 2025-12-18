# Fontshow

Fontshow generates a PDF catalog of the system fonts installed on the machine.
The project is organized as a **multi-stage, cross-platform pipeline** that
separates font discovery, metadata inference and LaTeX rendering.

---------------------------------------------------------------------

## Pipeline overview

```text
dump_fonts.py
  → font_inventory.json
parse_font_inventory.py
  → font_inventory_enriched.json
crea_catalogo.py
  → catalogo_font_sistema_<PLATFORM>_<DATE>_<NNN>.pdf
  ```

### Stage responsibilities

- dump_fonts.py
  OS-dependent discovery and metadata extraction.

- parse_font_inventory.py
  Cross-platform inference of scripts and languages.

- crea_catalogo.py
  Pure renderer producing LaTeX output.

---------------------------------------------------------------------

## Quick start

1. Generate inventory
   python3 scripts/dump_fonts.py

2. Enrich inventory
   python3 scripts/parse_font_inventory.py font_inventory.json

3. Generate LaTeX
   python3 crea_catalogo.py font_inventory_enriched.json

4. Build PDF
   lualatex catalogo_font_sistema_*.tex (run twice)

---------------------------------------------------------------------

## Sample text logic

- Emoji fonts → emoji-only samples
- Decorative fonts → family name
- Text fonts → language-aware samples

Languages supported include Arabic, Hebrew, Chinese, Japanese, Korean,
Armenian, Vietnamese, Coptic and Tigrinya.

---------------------------------------------------------------------

## Documentation

See the docs/ directory:

- architecture.md
- parse-font-inventory.md
- font-inventory-schema.md
- font-inventory.md
- fonttools-integration.md
- dump-fonts.md

---------------------------------------------------------------------

## Commit policy

Conventional Commits are enforced via hooks and CI.
