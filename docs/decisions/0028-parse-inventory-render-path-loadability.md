# ADR 0028: Parse-Inventory Render-Path Loadability

- Status: Accepted
- Date: 2026-04-04

## Context

Schema v1.3 currently stores one coarse per-font LuaLaTeX loadability
result under `loadability.lualatex`.

That coarse result is produced during `dump-fonts`, before
`parse-inventory` has attached:

- the resolved `typography.primary_script`
- the resolved `typography.render_policy`
- the inferred secondary scripts that the catalog renderer may later emit

As a result, the persisted loadability contract is weaker than the
catalog rendering contract:

- `dump-fonts` proves that a font loaded under one coarse probe
- `create-catalog` may later render multiple script-specific specimen
  blocks for the same font

This mismatch can allow a font to be persisted as loadable while a
later script-specific catalog specimen still fails under LuaLaTeX.

## Decision

We change the install-sensitive contract from:

- `dump-fonts` alone touches the current font and LuaLaTeX install

to:

- `dump-fonts` performs coarse per-font LuaLaTeX probing
- `parse-inventory` also touches the current install and refreshes
  script-aware render-path loadability after inference/specimen/render
  policy enrichment

Schema v1.4 extends `loadability.lualatex` so it also records
`render_variants`, an ordered array of script-aware validation records.

Each render-variant record stores:

- `script`
- `fontspec_opts`
- `attempted`
- `loadable`
- `reason`
- `runtime_fingerprint`
- `probe_input`

The existing top-level `loadability.lualatex` fields remain as a coarse
summary for compatibility. After `parse-inventory`, that summary is
allowed to reflect the primary render-path result for the current
environment.

## Consequences

Positive:

- Catalog rendering can distinguish primary-path success from
  secondary-script success.
- Secondary specimens can be gated on persisted evidence instead of
  cmap-only heuristics.
- The inventory records the actual render paths that were validated for
  the current install.

Costs:

- `parse-inventory` is no longer a pure JSON-only enrichment step.
- Running `parse-inventory` now depends on the current LuaLaTeX/fontspec
  environment when render-path validation is available.
- Inventory files produced on different TeX installations may diverge in
  their `render_variants` results.

Guardrails:

- `dump-fonts` coarse probing remains in place for backward-compatible
  summary behavior.
- `parse-inventory` render-path validation remains best-effort and must
  degrade cleanly when LuaLaTeX is unavailable.

## Follow-Up

- Align catalog specimen emission with persisted `render_variants`.
- Revisit the runtime fingerprint if install-level distinctions remain
  too coarse.
- Perform a branch-wide documentation sweep before merge to align user
  docs with the final implemented behavior.
