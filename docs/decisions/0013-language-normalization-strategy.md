# Decision 0013 - Language normalization strategy

**Date**: 25/01/2026
**Status**: Accepted

## Context

Fontshow extracts language information from multiple sources, most notably
Fontconfig. These sources provide language tags that:

- may include regional variants (e.g. `ar_IQ`, `pt-BR`)
- may contain annotations (e.g. `bem(s)`)
- may not be ISO-compliant
- may contain duplicates or inconsistent casing

At the same time, downstream consumers of the inventory require a stable,
normalized representation of supported languages.

## Decision

Fontshow distinguishes between two language-related fields:

### `languages_raw`

- Contains raw language tags as provided by Fontconfig or upstream tools
- Preserves original values verbatim
- Is never modified or normalized
- Exists for traceability and debugging purposes

### `languages`

- Contains normalized ISO language codes
- Is derived explicitly from `languages_raw`
- Is suitable for semantic processing and inference

Normalization is performed by a dedicated procedural function:
`normalize_languages()`.

## Normalization rules

The following rules are applied in order:

1. Split language tags on `-` or `_`
   - Example: `ar_IQ` → `ar`

2. Remove parenthesized suffixes
   - Example: `bem(s)` → `bem`

3. Convert to lowercase

4. Validate against ISO 639 language codes

5. Deduplicate while preserving order

## Dropped values

During normalization, entries may be discarded.
Each discarded value is recorded with a reason:

| Reason             | Meaning                               |
|--------------------|---------------------------------------|
| `invalid_format`   | Invalid or empty input                |
| `unknown_language` | Not a valid ISO language              |
| `variant_stripped` | Regional or annotated variant removed |
| `duplicate`        | Duplicate after normalization         |

The normalization function returns both:

- the normalized language list
- a structured list of dropped entries

## Logging responsibility

Normalization **does not perform logging**.

Logging is handled by the caller (typically `parse_inventory`), which may emit
warnings based on the returned `dropped` entries.

This separation ensures:

- deterministic behavior
- testability
- no side effects
- clean separation of concerns

## Non-goals

This design explicitly does NOT:

- infer languages automatically
- map languages to scripts
- attempt linguistic corrections
- guess user intent

All such logic belongs to higher-level inference steps.

## Consequences

- Language handling is explicit and auditable
- Raw data is always preserved
- Semantic processing is deterministic
- Future extensions are possible without breaking compatibility
