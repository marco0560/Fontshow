# Fontshow Inventory Schema

This document provides a **narrative and semantic description** of the
Fontshow inventory schema.
It complements the JSON Schema files and explains the *meaning* and
*intended usage* of the inventory fields.

The JSON Schema files remain the **authoritative source** for validation.
This document focuses on concepts, rationale, and evolution.

## Overview

A Fontshow inventory describes a collection of fonts discovered on a
system and the metadata extracted or inferred from them.

Two conceptual levels exist:

- **Raw inventory** (`schema_version = 1.0`)
- **Enriched inventory** (`schema_version = 1.1`)

The enrichment pipeline is incremental and non-destructive: new metadata
is added without removing or overriding existing information.


## Schema versions

### Schema 1.0 — Raw inventory

A raw inventory contains:

- font identity (path, family, style)
- best-effort metadata extracted from external tools (e.g. FontConfig)
- no inference or semantic interpretation

This version is primarily produced by `dump_fonts.py`.

### Schema 1.1 — Enriched inventory

Schema 1.1 extends the raw inventory with derived and inferred metadata.
It is typically produced by `parse_font_inventory.py`.

Enrichment steps include:

- Unicode block analysis
- Script and language inference
- Optional charset-driven diagnostics

Schema 1.1 remains backward compatible with schema 1.0.

## Coverage object

Most analytical metadata is grouped under the per-font `coverage` object.

The `coverage` object may contain a mix of:

- raw observations
- normalized representations
- derived, diagnostic metrics

All fields are optional unless otherwise stated.

## Charset-derived metadata (diagnostic)

Fontshow can optionally include and process FontConfig charset data.
This information is **diagnostic only** and does not currently affect
inference decisions.

### `normalized_charset`

A deterministic normalization of raw FontConfig charset ranges.

- Ranges are sorted and merged
- Codepoint count is computed
- No semantic interpretation is applied

This representation is idempotent and audit-friendly.

### `unicode_blocks_from_charset`

A mapping of Unicode block names to the number of codepoints covered
by the normalized charset.

This field:

- is derived from `normalized_charset`
- uses the existing Unicode block table
- does not replace other `unicode_blocks` data

### `script_coverage_from_charset`

An estimated per-script coverage ratio derived from charset-based
Unicode blocks.

Values are normalized ratios between 0.0 and 1.0 and represent
relative coverage only.

This field is:

- informational
- non-authoritative
- intended for diagnostics and future experimentation

---

## Design principles

The inventory schema follows these principles:

- **Additive evolution**
  New metadata is added without breaking existing consumers.

- **Separation of concerns**
  Raw data, normalized data, and inferred data are kept distinct.

- **Observability first**
  Diagnostic metadata is exposed explicitly before being used
  semantically.

- **Explicit versioning**
  Schema versions change only for semantic or contract-breaking updates.

## Future evolution

Future schema versions may be introduced if:

- charset-derived metrics influence inference
- precedence or fallback rules are defined
- new semantic guarantees are required

Until then, schema 1.1 is expected to evolve additively.

## Related files

- `docs/schema/inventory-1.1.schema.json`
- `fontshow/schema_validation.py`
- `fontshow/parse_font_inventory.py`
