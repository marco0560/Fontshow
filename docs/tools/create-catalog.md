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

Runtime LuaLaTeX loadability validation is available but **disabled by
default**.

Enable it explicitly with:

```bash
fontshow create-catalog --validate-loadability
```

Behavior:

- When the flag is **not** present, `create-catalog` renders directly
  from the inventory and performs no per-font LuaLaTeX probe.
- When the flag **is** present, Fontshow performs a best-effort
  per-font loadability check before rendering and skips fonts that fail.

Notes:

- This validation can be slow on large inventories because it spawns
  external LuaLaTeX checks.
- It is intended for diagnostics and troubleshooting, not for normal
  full-inventory catalog generation.
- The validation uses the same render policy as catalog generation so
  `fontspec` script options remain aligned between probing and final
  rendering.

## API reference

::: fontshow.cli.create_catalog
