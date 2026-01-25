# Fontshow Inventory Schema — v1.1

## Overview

Schema **v1.1** extends v1.0 with:

- structured warnings
- inference metadata
- normalized language and charset fields
- formal validation semantics

It is the canonical schema for all processed inventories.

---

## Top-level structure

```json
{
  "metadata": { ... },
  "fonts": [ ... ],
  "warnings": [ ... ]
}
```

### metadata

```json
{
  "schema_version": "1.1",
  "input_inventory_tool": "parse_inventory",
  "input_inventory_tool_version": "x.y.z",
  "inference_level": "low|medium|high"
}
```

---

## Font entry structure

### identity (optional)

In v1.1, `identity` is **optional** if alternative identifiers exist.

```json
{
  "file": "/path/to/font.ttf",
  "family": "Font Family",
  "style": "Regular"
}
```

### base_names (alternative)

```json
{
  "base_names": ["Font Family"]
}
```

Used when:

- identity is missing
- font metadata is incomplete
- data originates from legacy sources

---

## coverage block

### Raw fields

```json
{
  "languages_raw": ["en", "en_US"],
  "unicode_blocks": {...}
}
```

### Normalized fields

```json
{
  "languages": ["en"],
  "normalized_charset": {
    "ranges": [[32, 126]],
    "codepoints_count": 95
  }
}
```

---

## inference block

```json
{
  "level": "medium",
  "scripts": ["LATN"],
  "languages": ["en"],
  "unicode_blocks": { ... }
}
```

### Notes

- Generated automatically
- Never required for validity
- Never blocks processing

---

## warnings

### Structure

```json
{
  "code": "missing_identity",
  "message": "Font entry has no identity block",
  "severity": "warning"
}
```

### Severity levels

| Level     | Meaning                                |
|-----------|----------------------------------------|
| `info`    | Informational                          |
| `warning` | Non-fatal issue                        |
| `error`   | Semantic problem, processing continues |

⚠️ **Errors do NOT imply failure**

---

## Validation semantics

### validate_inventory_schema()

- Returns structured warnings
- Never raises exceptions
- Accepts imperfect real-world data

### _validate_inventory_schema_strict()

- Enforces JSON Schema strictly
- Raises `ValidationError`
- Used only in tests and tooling

---

## Design principles

- Real-world font data is imperfect
- Validation must be tolerant
- Errors must be visible but non-blocking
- Schema ≠ semantic correctness

---

## Status

✔ Current
✔ Production schema
✔ Backward-compatible with v1.0
✔ Used by `parse_inventory`
