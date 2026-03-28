# create-catalog

This module generates a printable LaTeX catalog from a normalized
Fontshow font inventory.

It is the final stage of the pipeline and focuses exclusively on
rendering and layout.

---

## Responsibilities

- Group fonts by family
- Select representative samples
- Render LaTeX blocks
- Generate a complete XeLaTeX/LuaLaTeX document

---

## Scope and non-responsibilities

The `create-catalog` stage is responsible for transforming a validated
inventory into final output artifacts.

It operates exclusively on **already validated input** and does not perform:

- font discovery
- metadata extraction
- inventory normalization
- semantic or structural validation
- error recovery for upstream stages

In particular:

- all validation errors must be resolved before this stage
- input data is assumed to be consistent and complete
- failures at this stage indicate output or rendering issues, not data errors

This separation ensures that:

- validation logic remains centralized
- output generation remains deterministic
- failures are easy to attribute to their correct stage

---

## Inventory Diagnostics

During catalog generation, Fontshow may emit lightweight diagnostics
about the input inventory before rendering begins.

These diagnostics are informational and help identify inventories with
poor language coverage, but they do not introduce a separate strict-mode
CLI contract for `create-catalog`.

Validation of inventory structure and semantics remains the
responsibility of upstream stages such as `parse-inventory` and
`validate-inventory`.

---

## Effective filtering behavior

`create-catalog` now distinguishes clearly between normal execution and
test-subset execution.

- Plain `fontshow create-catalog` uses the full inventory.
- `fontshow create-catalog --test` uses the platform-specific
  `DEFAULT_TEST_FONTS` subset.
- `fontshow create-catalog --test-font NAME` restricts rendering to the
  explicitly requested family names.
- `fontshow create-catalog --test --test-font NAME` combines the
  default test subset with additional explicit families.
- `fontshow create-catalog --list-test-fonts` reports the effective test
  subset and exits without generating a catalog.

Inventory diagnostics are emitted for the **effective render set** after
filtering, not for the full loaded inventory.

---

## Loadability Validation

`create-catalog` now uses **persisted LuaLaTeX loadability** from the
inventory by default.

Behavior:

- When persisted loadability is present and the runtime fingerprint
  matches the current environment, `create-catalog` trusts the
  persisted per-font `loadability.lualatex` state.
- When persisted loadability is missing, incomplete, or stale,
  `create-catalog` falls back to best-effort runtime LuaLaTeX probing
  for the affected fonts only.
- Fonts proven unloadable are skipped deterministically and reported in
  the generated `.tex` output under an unloadable-font section.

Notes:

- The normal fast path is to reuse persisted loadability produced by
  `dump-fonts`.
- Runtime fallback remains slower because it still uses per-font probes
  in the catalog stage.
- The fallback path uses the same render policy as catalog generation so
  `fontspec` script options remain aligned between probing and final
  rendering.
- There is no longer a `--validate-loadability` flag on
  `create-catalog`.

## API reference

::: fontshow.cli.create_catalog
