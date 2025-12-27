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

Derived values such as the total number of fonts must not be stored in
metadata, as they can be recomputed by downstream stages.

---

## Global metadata

The `metadata` object contains information about the context in which
the inventory was generated.

### Inventory metadata and schema versioning

The font inventory includes a `metadata` section describing the context in
which the inventory was generated.

This section contains:

- a `schema_version` identifying the inventory format
- the name and version of the tool that generated the inventory
- environment information (host, OS, execution context)

All metadata fields are optional and must be treated as non-authoritative.
They are intended for debugging, reproducibility, and diagnostic purposes
only.

Downstream consumers must not assume the presence of any metadata field.

### Fields

- **`schema_version`** (`string`)
  Version identifier of the inventory schema (e.g. `"1.0"`).

- **`tool`** (`string`)
  Identifier of the tool that generated the inventory (e.g. `dump_fonts`).

- **`tool_version`** (`string`)
  Version of Fontshow used to generate the inventory.

- **`generated_at`** (`string`, ISO 8601, UTC)
  Timestamp of inventory generation.

- **`environment`** (`object`, optional)
  Information about the execution environment.

  Typical subfields include:

  - `hostname`
  - `username`
  - `os`
  - `kernel`
  - `platform`
  - `execution_context.type` (`native`, `wsl`, `container`, `vm`, `unknown`)

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
  "sample_text": null,
  "raw": { ... },
  "coverage": { ... },
  "classification": { ... }
}
```

Not all fields are mandatory. Optional fields may be absent if the
corresponding information could not be determined.

Some inventory entries may represent charset-only information rather than
individual fonts. These entries may lack identifying fields such as
`identity.family` or `base_names`.

Such entries are valid and may appear when extended Fontconfig data is
included, but they are not intended to be used for font selection or catalog
generation.

---

### identity.family

- **Type**: string
- **Required**: no
- **Description**: Human-readable family name as extracted from font metadata.
  This field is not used for structural validation.

---

### charset (optional)

The `charset` field contains Unicode coverage information as reported by
Fontconfig when the inventory is generated with the option
`--include-fc-charset`.

This field is optional and may be `null` when:

- Fontconfig is not available (e.g. Windows native)
- the font does not expose charset information
- the option `--include-fc-charset` is not used

When present, the structure is:

```json
"charset": {
  "source": "fontconfig",
  "ranges": ["0000-007F", "0100-017F"]
}
```

The ranges represent **declared Unicode coverage** as advertised by
Fontconfig and should be considered complementary to the `coverage`
field, which is derived directly from font tables using FontTools.

## Sample text

Some font files may include an **embedded sample or demonstration text** intended to showcase the font.

This information is **optional** and **not guaranteed to be present** in all font files.

When available, it is extracted verbatim from the font metadata without modification.

---

### Field: `sample_text`

| Attribute | Type | Description |
|---------|------|-------------|
| `sample_text` | object \| null | Optional sample text information embedded in the font |

If the font does not provide any sample text, this field is set to `null`.

---

### `sample_text` object structure

| Field | Type | Description |
|------|------|-------------|
| `source` | string | Origin of the sample text |
| `text` | string | The sample text content |

---

### `sample_text.source`

Allowed values:

- `font`
  The sample text is embedded directly in the font metadata.

- `system`
  The sample text is generated externally by the system or tooling.

- `none`
  No sample text is available.
  In the inventory, this condition is represented by `sample_text: null`.

---

### Example (sample text available)

```json
{
  "sample_text": {
    "source": "font",
    "text": "The quick brown fox jumps over the lazy dog"
  }
}
```

---

### Example (no sample text)

```json
{
  "sample_text": null
}
```

---

### Notes and constraints

- The sample text is **not normalized**, translated, or altered.
- Absence of sample text is **not considered an error**.
- Downstream stages (catalog generation, previews) may choose whether and how to use this field.
- The presence or absence of this field must not affect pipeline correctness.


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

### family

- **Type**: string
- **Required**: yes
- **Description**: Canonical font family name used for validation, grouping
  and indexing. This field is mandatory for a font entry to be considered valid.

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

The inventory format is explicitly versioned via the `metadata.schema_version`
field.

The schema version is independent from the Fontshow tool version.

Non-breaking changes may add new optional fields without changing the schema
version. Breaking changes require a schema version bump and corresponding
documentation updates.

Downstream consumers must tolerate unknown schema versions and missing fields,
issuing warnings when appropriate but never aborting execution.

---

## Summary

The Fontshow data model is intentionally explicit and extensible.

It serves as:

- a stable contract between pipeline stages,
- a serialization format for caching and inspection,
- a foundation for external tools consuming font metadata.
