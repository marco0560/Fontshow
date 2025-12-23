# Data Dictionary

## Overview

This document defines the **data model and contracts** used throughout
the Fontshow pipeline.

The central artifact is the **font inventory**, a JSON-compatible
structure that is progressively enriched by each pipeline stage.

The purpose of this document is to:

- describe the structure of the inventory,
- define the meaning of each field,
- clarify which module is responsible for producing each piece of data.

This document is normative: downstream consumers should rely on the
definitions provided here.

---

## Inventory structure

At the top level, the font inventory is a JSON object with two main keys:

- `metadata`
- `fonts`

```json
{
  "metadata": { ... },
  "fonts": [ ... ]
}
```

---

## Global metadata

The `metadata` object contains information about the context in which
the inventory was generated.

### Fields

- **`generator`** (`string`)
  Identifier of the tool that generated the inventory (e.g. `Fontshow`).

- **`version`** (`string`)
  Version of the generator.

- **`timestamp`** (`string`, ISO 8601)
  Generation time of the inventory.

- **`platform`** (`string`)
  Operating system identifier (e.g. `linux`, `windows`).

- **`font_count`** (`integer`)
  Total number of font faces discovered.

---

## Font entries

The `fonts` array contains one entry per font face.

Each entry is a dictionary describing a single font face extracted from
a font file or a font collection.

```json
{
  "file": "...",
  "index": 0,
  "family": "...",
  "style": "...",
  "format": "...",
  "raw": { ... },
  "coverage": { ... },
  "classification": { ... }
}
```

Not all fields are mandatory. Optional fields may be absent if the
corresponding information could not be determined.

---

## File and identity fields

These fields identify the physical font resource.

- **`file`** (`string`)
  Absolute or normalized path to the font file.

- **`index`** (`integer`)
  Face index within a TrueType Collection (TTC).
  For single-face fonts, this is usually `0`.

- **`family`** (`string`)
  Font family name as reported by the font metadata.

- **`style`** (`string`)
  Style or subfamily name (e.g. `Regular`, `Bold Italic`).

- **`format`** (`string`)
  Font format identifier (e.g. `TTF`, `OTF`, `TTC`).

---

## Raw metadata

The `raw` section contains low-level metadata extracted directly from
the font binary.

This data is produced exclusively by **`dump_fonts`**.

Typical contents include:

- name table entries,
- OS/2 table fields,
- Unicode range flags,
- basic typographic metrics.

The structure of `raw` is intentionally flexible and may vary depending
on font format and available tables.

Downstream modules must treat this section as opaque and read-only.

---

## Coverage information

The `coverage` section describes Unicode coverage information.

This section is initially populated by **`dump_fonts`** and may be
refined by **`parse_font_inventory`**.

Typical fields include:

- covered Unicode ranges,
- lists of representative codepoints,
- script-level coverage summaries.

Coverage data is used as the basis for script and language inference.

---

## Classification and inference

The `classification` section contains semantic information inferred
from coverage and metadata.

This section is produced by **`parse_font_inventory`**.

Typical fields include:

- **`scripts`** (`list[string]`)
  Writing systems supported by the font (e.g. `Latin`, `Cyrillic`).

- **`languages`** (`list[string]`)
  Languages likely supported by the font.

- **`primary_script`** (`string`, optional)
  The dominant script inferred for the font.

- **`confidence`** (`float`, optional)
  Confidence score associated with inference results.

Inference fields are heuristic by nature and should be interpreted as
best-effort indicators rather than absolute guarantees.

---

## Rendering-related fields

Some fields are added or derived specifically to support rendering.

These fields are typically consumed by **`create_catalog`** and may
include:

- grouping hints,
- sample text selection metadata,
- script prioritization flags.

Rendering-related fields must not affect upstream inference logic.

---

## Optional and missing fields

Fontshow is designed to tolerate incomplete data.

Rules:

- optional fields may be missing,
- missing fields must never cause downstream crashes,
- absence of data should result in degraded output quality, not failure.

Consumers of the inventory must always check for field presence.

---

## Versioning and compatibility

The inventory format is versioned implicitly via the generator version
stored in `metadata.version`.

Breaking changes to the inventory structure should be accompanied by:

- a version bump,
- explicit documentation updates,
- migration notes if applicable.

---

## Summary

The Fontshow data model is intentionally explicit and extensible.

It serves as:

- a stable contract between pipeline stages,
- a serialization format for caching and inspection,
- a foundation for external tools consuming font metadata.
