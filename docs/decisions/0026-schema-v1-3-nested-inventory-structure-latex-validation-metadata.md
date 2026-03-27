# Decision 0026 - Schema v1.3 nested inventory structure and LaTeX validation metadata

**Date**: 27/03/2026
**Status**: Accepted

## Context

Schema v1.2 consolidated the inventory contract, but later hardening work
introduced new requirements that no longer fit well in the flat v1.2 layout.

The next loadability-related work requires the inventory to persist:

- per-font LuaLaTeX loadability state
- inventory-level LaTeX runtime metadata
- a runtime fingerprint for invalidation
- render-policy provenance

At the same time, v1.2 still mixed several distinct concerns at the top level
of each font entry:

- technical numeric metrics
- specimen and rendering-oriented fields
- future engine-specific validation state

That flat structure made schema evolution harder to reason about, and it
blurred the distinction between:

- raw technical facts about the font
- typography-facing rendering metadata
- validation/runtime metadata tied to the LaTeX toolchain

The project also needs the schema itself to serve as a stronger
documentation source. For that reason, v1.3 should carry explicit
descriptions for the schema fields instead of relying only on prose
outside the JSON Schema file.

## Decision

The project adopts **Fontshow Inventory Schema v1.3** as the new
authoritative inventory schema and updates the codebase accordingly.

The v1.3 changes are:

### 1. Group raw numeric font metrics under `metrics`

Per-font technical metrics move from the top level into:

- `metrics.units_per_em`
- `metrics.ascent`
- `metrics.descent`
- `metrics.weight_class`
- `metrics.width_class`
- `metrics.italic_angle`
- `metrics.is_fixed_pitch`
- `metrics.glyph_count`

This separates technical measurements from rendering-oriented metadata.

### 2. Group rendering-oriented fields under `typography`

Per-font specimen and script/render-policy fields live under:

- `typography.sample_text`
- `typography.specimen_text`
- `typography.specimen_strategy`
- `typography.specimen_glyph_count`
- `typography.specimen_rejection_reason`
- `typography.primary_script`
- `typography.script_display_name`
- `typography.render_policy`
- `typography.script_source`
- `typography.opentype_features`

This makes it explicit that these fields exist for rendering, specimen
selection, and typography-facing diagnostics rather than core identity.

### 3. Introduce explicit per-font loadability state

Per-font persisted LuaLaTeX state lives under:

- `loadability.lualatex.attempted`
- `loadability.lualatex.loadable`
- `loadability.lualatex.reason`
- `loadability.lualatex.runtime_fingerprint`
- `loadability.lualatex.probe_input`

This keeps engine-specific loadability extensible and prevents ad hoc
top-level keys from accumulating in the font entry.

### 4. Introduce inventory-level LaTeX validation metadata

Inventory-wide LaTeX runtime information lives under:

- `metadata.validation.lualatex.attempted`
- `metadata.validation.lualatex.engine`
- `metadata.validation.lualatex.engine_version`
- `metadata.validation.lualatex.luaotfload_version`
- `metadata.validation.lualatex.fontspec_version`
- `metadata.validation.lualatex.polyglossia_version`
- `metadata.validation.lualatex.runtime_fingerprint`
- `metadata.validation.lualatex.render_policy_version`

This distinguishes global runtime/toolchain facts from font-specific
loadability results.

### 5. Make schema descriptions first-class

The v1.3 schema file must carry `description` fields throughout the
active schema surface so the generated schema documentation can derive
field explanations directly from the schema source of truth.

### 6. Keep a single authoritative schema version

The project continues to use a single active schema version tracked by
the repository constant and validated strictly at load time. The codebase
does not keep v1.2 as a second active contract.

## Consequences

### Positive

- The inventory model now separates identity, metrics, typography, and
  validation concerns more clearly.
- Future loadability persistence work has an explicit schema target.
- Inventory-wide LaTeX metadata and per-font loadability no longer
  compete for the same top-level namespace.
- Schema-derived documentation becomes more useful because field
  descriptions live in the JSON Schema itself.
- Future engine-specific validation state can be extended under
  `loadability` and `metadata.validation` without flattening the model.

### Negative

- This is a breaking schema change from v1.2 to v1.3.
- Existing fixtures, validators, producers, and consumers must migrate
  together.
- Inventories generated under v1.2 must be regenerated to satisfy the
  new contract.

## Migration

- Switch the authoritative schema version to `1.3`.
- Update all inventory producers to emit nested `metrics`,
  `typography`, and `loadability` sections.
- Update all inventory consumers and validators to read the v1.3 shape.
- Regenerate schema documentation from the v1.3 JSON schema file.
- Do not keep parallel active support for v1.2 in runtime validation.

## Related

- Issue #65 — Schema v1.3: persist loadability metadata and normalize
  typography-oriented inventory fields
- Issue #66 — Persist LuaLaTeX loadability in dump-fonts via batched
  probing and report unloadable fonts in create-catalog
- ADR 0020 — Schema v1.2 Unification and Deprecation of Previous Versions

## Notes

This decision does not implement batched probing or final persisted
loadability behavior by itself. It establishes the schema contract that
subsequent loadability work can rely on.
