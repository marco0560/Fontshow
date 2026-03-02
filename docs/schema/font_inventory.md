# Font Inventory Schema v1.2

## Overview

Schema **v1.2** is the single authoritative schema for the Fontshow inventory.
Previous schemas **v1.0** and **v1.1** are deprecated and archived.

This schema guarantees:

* Deterministic inventory structure
* Strict typing
* Canonical font identity
* Robust specimen generation (Issue #54)
* Reproducibility across systems
* Simplified validation and maintenance

---

## Root Structure

```json
{
  "metadata": {...},
  "fonts": [...]
}
```

---

## Metadata

Required fields:

* `schema_version` = `"1.2"`
* `input_inventory_tool`
* `input_inventory_tool_version`
* `inference_level`
* `run_environment`

### run_environment

Identifies the system where Fontshow executed:

* `os`
* `os_release`
* `kernel`
* `machine`
* `python_version`
* `hostname`

---

## Font Entry

Each entry represents **one font face**.

Multiple faces in a single font file (TTC/collections) are represented by **multiple entries sharing the same `path`**.

---

## Canonical Path Rule

* Exactly one `path` per font entry
* No duplicated path in identity
* Multiple faces → same path, different identity

---

## Deterministic Identity (Required)

* `family`
* `subfamily`
* `typographic_subfamily`
* `full_name`
* `postscript_name`
* `version_string`
* `unique_font_id`

Ensures stable, cross-platform identification.

---

## Technical Core Metrics (Required)

* `units_per_em`
* `ascent`
* `descent`
* `weight_class`
* `width_class`
* `italic_angle`
* `is_fixed_pitch`
* `glyph_count`

Used for diagnostics and reproducibility.

---

## Coverage, Inference, Charset

Preserved from previous schemas; structure unchanged.

---

## Embedded Sample Text

```json
sample_text = {
  "source": "font",
  "text": ...
}
```

Raw internal sample from font, not guaranteed valid for rendering.

---

## Deterministic Specimen (Issue #54)

Required fields:

* `specimen_text`
* `specimen_strategy` (`internal | script | cmap | deferred`)
* `specimen_glyph_count`

Optional:

* `specimen_rejection_reason`

### Strategy

1. Internal sample (validated)
2. Script-aware sample
3. Cmap-driven fallback (guaranteed safe)

Ensures LuaLaTeX subset never fails.

---

## Font-Level Warnings (Optional)

```json
warnings = [
  { code, message, severity }
]
```

Severity enum: `info | warning | error`.

---

## Determinism Guarantees

* Same font → identical specimen across runs
* No randomness
* Canonical identity
* Strict schema validation

---

## Migration

* Regenerate inventory using current pipeline
* v1.0 and v1.1 inventories unsupported

---

## Related

* ADR 0020 — Schema v1.2 Unification
* ADR 0019 — Enum JSON representation
* Issue #54 — Robust specimen fallback
