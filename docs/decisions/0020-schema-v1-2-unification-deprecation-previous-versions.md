# Decision 0020 - Schema v1.2 Unification and Deprecation of Previous Versions

**Date**: 16/02/2026
**Status**: Accepted

## Context

The Fontshow suite historically supported multiple JSON schema versions for the font inventory:

* v1.0
* v1.1

Over time, this created:

* Conditional validation logic
* Backward-compatibility branches
* Increased code complexity
* Reduced determinism
* Maintenance overhead

Issue #54 (robust specimen fallback for LuaLaTeX safety) required the introduction of new **mandatory deterministic fields**, which cannot be safely supported under the previous schemas without further fragmentation.

Additionally, prior schema structure contained architectural weaknesses:

* Dual representation of font file path
* Incomplete deterministic font identity
* Weak typing in some areas
* Lack of explicit execution environment metadata
* Absence of structured font-level warnings

To support deterministic, fail-safe, and maintainable behavior across the entire Fontshow pipeline, a schema unification was required.

---

## Decision

The project adopts **Font Inventory Schema v1.2** as the **single authoritative schema** for the entire Fontshow suite.

The following changes are introduced:

### 1. Schema Unification

* Schema **v1.2 becomes the only supported schema**
* Schema versions **v1.0 and v1.1 are deprecated**
* Inventory validation must enforce `schema_version == "1.2"`

### 2. Deterministic Specimen Fields (Issue #54)

Each font entry must include:

* `specimen_text`
* `specimen_strategy`
* `specimen_glyph_count`

Optional:

* `specimen_rejection_reason`

These fields ensure LuaLaTeX-safe specimen generation.

### 3. Canonical File Path

* Exactly one canonical `path` per font entry
* Any duplicated path representation is removed
* Multi-face fonts remain represented by multiple entries sharing the same file path

### 4. Deterministic Font Identity

Each font entry must include:

* `family`
* `subfamily`
* `typographic_subfamily`
* `full_name`
* `postscript_name`
* `version_string`
* `unique_font_id`

This ensures stable face identification across environments and TTC collections.

### 5. Technical Core Metrics

Each font entry must include:

* `units_per_em`
* `ascent`
* `descent`
* `weight_class`
* `width_class`
* `italic_angle`
* `is_fixed_pitch`
* `glyph_count`

These improve reproducibility and diagnostics.

### 6. Metadata Preservation and Extension

The `metadata` section is preserved and extended with:

* `input_inventory_tool`
* `input_inventory_tool_version`
* `inference_level`
* `run_environment` (system identification)

### 7. Structured Font-Level Warnings

Font entries may optionally include:

* `warnings[]` with typed severity (`info`, `warning`, `error`)

### 8. Strict Typing

Schema v1.2 enforces strict typing where appropriate and removes legacy tolerance.

---

## Consequences

### Positive

* Simplified validation logic
* Deterministic and reproducible inventories
* Removal of legacy compatibility branches
* Improved maintainability
* Stronger identity guarantees
* Better diagnostics and traceability
* Safer LuaLaTeX rendering
* Single schema across entire suite

### Negative (Intentional)

* Breaking change: legacy inventories unsupported
* Inventories must be regenerated
* Validator will hard-fail on schema != 1.2

---

## Migration

* Regenerate inventory using `parse-inventory`
* Legacy inventories (v1.0 / v1.1) are not supported
* No automatic migration is provided

---

## Related

* Issue #54 — Robust specimen fallback
* ADR 0019 — Enum JSON representation

---

## Notes

This decision establishes the foundation for deterministic schema evolution. Future schema revisions must preserve:

* Deterministic behavior
* Single authoritative schema
* Strong typing
* Explicit identity
* Backward compatibility only when explicitly justified

--- End of ADR 0020 ---
