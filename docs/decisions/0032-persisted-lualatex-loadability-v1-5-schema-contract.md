# Decision 0032 - Persisted LuaLaTeX Loadability v1.5 Schema Contract

**Date**: 24/04/2026
**Status**: Accepted

## Context

ADR 0028 changed `parse-inventory` from a pure JSON enrichment step into a
step that may refresh render-path loadability against the current LuaLaTeX and
fontspec installation. The current v1.5 schema makes persisted per-font
LuaLaTeX loadability state part of the inventory contract.

Evidence:

- `docs/decisions/0028-parse-inventory-render-path-loadability.md:36-39`
  states that `parse-inventory` refreshes script-aware render-path loadability
  after inference/specimen/render-policy enrichment.
- `docs/decisions/0028-parse-inventory-render-path-loadability.md:41-48`
  states that render variants store script, fontspec options, specimen, and
  loadability result.
- `docs/decisions/0028-parse-inventory-render-path-loadability.md:72-75`
  states that `parse-inventory` now depends on the current LuaLaTeX/fontspec
  environment when render-path validation is available.
- `src/fontshow/schema/inventory_v1_5.json:393-408` requires per-font
  `loadability.lualatex` fields including `attempted`, `loadable`, `reason`,
  `runtime_fingerprint`, `probe_input`, and `render_variants`.
- `src/fontshow/schema/inventory_v1_5.json:432-434` describes
  `render_variants` as per-render-path LuaLaTeX validation results.
- `tests/test_output_schema_invariants.py:120-127` includes
  `loadability.lualatex.render_variants` in the minimal valid v1.5 inventory.

## Decision

Persisted LuaLaTeX loadability metadata is part of the v1.5 inventory schema
contract.

Every font entry in a canonical v1.5 inventory must include
`loadability.lualatex` with the fields required by the schema, including
`render_variants`.

`render_variants` records the script-aware render paths evaluated for the
current runtime context. It may be empty when probing was not attempted or no
variant evidence is available, but the field itself is required.

Runtime-sensitive values must be stored explicitly rather than inferred
silently at catalog-render time.

## Consequences

- Inventory files can carry environment-sensitive LuaLaTeX evidence.
- Inventories produced on different TeX installations may differ in
  loadability metadata.
- Catalog rendering can consume persisted render-path evidence instead of
  relying only on cmap or specimen heuristics.
- Tests for minimal valid inventories must include the required loadability
  structure.
- Future changes to loadability shape require schema, tests, and ADR updates.
