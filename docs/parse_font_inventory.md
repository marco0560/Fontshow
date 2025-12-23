# parse_font_inventory

This module enriches the raw font inventory produced by `dump_fonts`
by performing script, language, and writing-system inference.

It operates purely on JSON data and never inspects font binaries.

---

## Responsibilities

- Infer primary script(s)
- Infer language coverage
- Normalize Unicode coverage information
- Attach inference metadata to each font entry

---

## API reference

::: fontshow.parse_font_inventory
