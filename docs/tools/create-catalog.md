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

## API reference

::: fontshow.cli.create_catalog
