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

## Language normalization and validation

### Language tags processing

Fontshow performs language processing as part of inventory normalization.
This process is intentionally split into **normalization** and **validation**.

These steps apply only to language-related fields and do not alter schema
structure.

---

### Normalization

Normalization is applied to language tags derived from font metadata.

Its goals are:

- increase consistency across heterogeneous inputs
- normalize casing and structure
- map deprecated tags to modern equivalents where possible

Normalization is **non-destructive** and best-effort.

Examples of normalization:

- canonical casing (`en-us` → `en-US`)
- deprecated subtags mapped to current forms
- removal of unsupported private extensions

Fontshow applies **non-destructive normalization** to language tags in order to:

- align non-standard or deprecated tags to modern equivalents
- ensure consistent downstream processing
- preserve as much original semantic meaning as possible

Normalization may include:

- case normalization
- script or region canonicalization
- replacement of deprecated subtags

Normalization **does not imply validation success**.

### Deprecated vs obsolete vs invalid tags

Language tags are classified as:

| Category   | Meaning                     | Behavior                               |
|------------|-----------------------------|----------------------------------------|
| Deprecated | Tag is valid but superseded | Accepted, normalized, warning emitted  |
| Obsolete   | Tag is no longer defined    | Accepted (non-strict), warning emitted |
| Invalid    | Not RFC-compliant           | Rejected in strict mode                |

---

### Validation modes

Fontshow supports two validation modes.

#### Permissive (default)

- Invalid or deprecated tags are accepted
- Warnings are emitted
- Processing continues
- Normalized values are used when possible

#### Strict (`--strict-bcp47`)

- Only RFC-compliant BCP-47 tags are allowed
- Deprecated or malformed tags cause failure
- No silent normalization is applied
- Processing aborts on first violation

Strict mode affects **validation only** and does not alter the schema.

---

### Design criteria

- Normalization ≠ validation
- Validation ≠ enforcement
- Enforcement is explicit and opt-in
- Behavior must be observable and documented

---

### Non-goals

- Automatic language inference
- Linguistic correctness guarantees
- Silent mutation of user data

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

---
