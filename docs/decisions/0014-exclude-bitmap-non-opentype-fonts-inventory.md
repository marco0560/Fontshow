# Decision 0014 - Exclude bitmap / non-OpenType fonts from inventory

**Date**: 26/01/2026
**Status**: Accepted

## Context

Fontshow builds a structured font inventory intended for:

- OpenType / TrueType analysis
- Unicode coverage inspection
- LaTeX and typographic catalog generation
- Semantic validation of font metadata

During testing, it was observed that the system font database (via Fontconfig)
may include legacy bitmap fonts (e.g. `.pcf`, `.pcf.gz`) that:

- are not OpenType or TrueType fonts
- are not supported by fontTools
- cannot be used by LuaLaTeX or HarfBuzz
- do not expose reliable family/style metadata
- often lack scalable outlines

These fonts appear in Fontconfig results but are not usable for Fontshow’s
intended purposes.

## Decision

Fontshow **explicitly excludes bitmap and non-OpenType fonts** from the
inventory generation phase.

A font is excluded if:

- `fonttools` cannot parse it, or
- its detected format is not OpenType / TrueType

Such fonts are ignored during `dump-fonts` and never reach later pipeline
stages.

## Rationale

- Bitmap fonts cannot be used by LuaLaTeX
- They cannot be analyzed semantically
- They introduce invalid or incomplete entries
- They break inventory validation invariants
- Their inclusion provides no practical value

This decision keeps the inventory:

- semantically consistent
- usable for downstream tooling
- aligned with Fontshow’s purpose

## Consequences

- Bitmap fonts (e.g. PCF) are silently skipped
- Inventory size is reduced but semantically correct
- No changes are required in `parse-inventory`
- No schema changes are needed

## Alternatives considered

### Accept bitmap fonts

Rejected — leads to invalid or unusable inventory entries.

### Treat bitmap fonts as warnings

Rejected — increases complexity without benefit.

### Filter at parse time

Rejected — less clear separation of responsibilities.

---

## Notes

This decision does **not** prevent future support for bitmap fonts,
but such support would require a separate data model and rendering path.
