# Decision 0027 - Catalog low-information specimen rendering policy

**Date**: 04/04/2026
**Status**: Accepted

## Context

Catalog generation now renders many more families from the persisted
inventory than the historical TeX-side bookkeeping model assumed.

That broader coverage exposes two distinct classes of low-value output:

- text fonts whose stored primary specimen is technically valid but too
  short to be useful in the catalog
- specialized fonts such as icon or symbol faces whose metadata does
  not justify pretending they are normal text fonts

The catalog renderer therefore needs a deterministic policy for
handling low-information primary specimens without misrepresenting the
font.

This is no longer an incidental implementation detail because the rule
affects the visible PDF artifact and the catalog contract seen by users.

## Decision

The catalog renderer adopts the following low-information specimen
policy:

### 1. Keep useful stored primary specimens unchanged

If the persisted primary specimen is already above the renderer
usefulness threshold, render it unchanged.

### 2. Prefer curated script specimens for writing fonts

If the persisted primary specimen is too short to be useful and the
font still behaves like a text font, try the ontology-backed predefined
specimen for the primary script and filter it through the font cmap.

If that curated specimen survives the existing renderer threshold, use
it instead of the stored low-information specimen.

### 3. Do not fabricate text for specialized fonts

If the persisted primary specimen is too short to be useful, no curated
primary-script replacement survives, and the font behaves like a
specialized non-text face, suppress the text specimen and render a
compact specialized-font notice instead.

The current specialized-font classifier is intentionally conservative:

- low-information primary specimen
- no declared or inferred languages
- specimen strategy indicates cmap-driven or validated fallback output

### 4. Keep the rule renderer-local

This policy changes catalog presentation only. It does not modify the
persisted inventory specimen-selection pipeline or schema.

## Consequences

### Positive

- writing fonts get more informative catalog specimens when curated
  script samples are available
- specialized symbol-like fonts are no longer misrepresented as if they
  had meaningful text coverage
- output remains deterministic because both the classifier and curated
  fallback path are metadata- and cmap-driven

### Negative

- some fonts now render a specialized notice instead of a specimen
  block, which changes the visible PDF contract
- specialized-font classification is conservative and may still require
  future refinement as more edge cases are observed

## Related

- Issue #70 — feat(catalog): gate TOC and clickable navigation behind a
  flag
- Issue #59 — Create selective archives
- ADR 0022 — Fontshow — Specimen Inference Inputs Matrix v1.0
- ADR 0026 — Schema v1.3 nested inventory structure and LaTeX
  validation metadata
