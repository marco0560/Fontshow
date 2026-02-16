# Fontshow Inventory Schema — v1.0

## Overview

The **inventory v1.0 schema** defines the minimal structure produced by
`fontshow dump-fonts` and consumed by early stages of the processing pipeline.

This schema represents **raw font discovery output** and does not include
inference, normalization, or semantic enrichment.

It is intentionally permissive and designed to tolerate partial or
incomplete font metadata.

---

## Top-level structure

```json
{
  "metadata": {
    "schema_version": "1.0"
  },
  "fonts": [ ... ]
}
```

### Required fields

| Field                     | Type   | Description          |
|---------------------------|--------|----------------------|
| `metadata.schema_version` | string | Must be `"1.0"`      |
| `fonts`                   | array  | List of font entries |

---

## Font entry structure

Each entry in `fonts` must contain:

```json
{
  "identity": { ... },
  "coverage": { ... }
}
```

### identity (required)

```json
{
  "file": "/path/to/font.ttf",
  "family": "Font Family",
  "style": "Regular"
}
```

| Field    | Type   | Required | Notes         |
|----------|--------|----------|---------------|
| `file`   | string | yes      | Absolute path |
| `family` | string | yes      | Font family   |
| `style`  | string | yes      | Font style    |

---

### coverage (required)

Raw data collected from font analysis tools.

Typical fields:

```json
{
  "unicode_blocks": { "Basic Latin": 95 },
  "scripts": ["Latn"]
}
```

No normalization or validation is performed at this stage.

---

## Validation semantics

### What is enforced

- Structural presence of required fields
- Basic type correctness

### What is NOT enforced

- Semantic correctness
- Charset normalization
- Language inference
- Script inference

---

## Notes

- This schema represents **raw inventory**
- No inference or enrichment is expected
- Used as input for `parse_inventory`
- Forward-compatible with v1.1

---

## Status

✔ Stable
✔ Backward-compatible
✔ Used for ingestion only
