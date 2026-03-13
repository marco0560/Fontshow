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

## Semantic Validation

During catalog generation, semantic validation is performed on the
enriched inventory.

By default:

<!-- cheatsheet:start -->
- semantic issues are reported as warnings
- catalog generation continues

When `--strict-semantic` is enabled:

- semantic warnings are treated as errors
- catalog generation aborts
- a non-zero exit code is returned
<!-- cheatsheet:end -->

This mode does not affect:

- schema validation
- language normalization
- parsing or discovery stages

## API reference

::: fontshow.cli.create_catalog
