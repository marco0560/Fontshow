# Decision 0031 - Inventory Schema v1.5 Authority and Compatibility Contract

**Date**: 24/04/2026
**Status**: Accepted

## Context

Earlier schema decisions document v1.2 and v1.3 as authoritative at the time
they were accepted, and ADR 0028 documents render-path loadability changes
that extend schema behavior. The current repository schema and tests now use
Inventory Schema v1.5.

Evidence:

- `docs/decisions/0020-schema-v1-2-unification-deprecation-previous-versions.md:37-45`
  adopted schema v1.2 and deprecated v1.0/v1.1.
- `docs/decisions/0026-schema-v1-3-nested-inventory-structure-latex-validation-metadata.md:39-40`
  adopted Inventory Schema v1.3 as authoritative.
- `src/fontshow/schema/inventory_v1_5.json:3-5` identifies the current schema
  as `Fontshow Inventory Schema v1.5`.
- `src/fontshow/schema/inventory_v1_5.json:27-30` requires
  `metadata.schema_version` to be the constant `1.5`.
- `tests/test_output_schema_invariants.py:47-48` constructs the minimal valid
  test inventory with `"schema_version": "1.5"`.
- `tests/test_output_schema_invariants.py:155-156` asserts that enriched
  output metadata uses schema version `1.5`.

## Decision

Fontshow Inventory Schema v1.5 is the current authoritative inventory schema.

All inventory-producing and inventory-consuming code must treat
`metadata.schema_version == "1.5"` as the current canonical contract unless a
future ADR supersedes this decision.

Schema versions documented in earlier ADRs remain historical migration
records. They do not supersede the current v1.5 schema files or tests.

Compatibility behavior for older schemas must be explicit in code and tests.
No implicit compatibility fallback is assumed.

## Consequences

- The schema source of truth is aligned with the current repository state.
- Changes to inventory structure after v1.5 require a new ADR or an explicit
  superseding decision.
- Tests that construct or validate canonical inventories must use v1.5 unless
  they are specifically testing legacy rejection or migration behavior.
- Documentation that describes current inventory shape must not present v1.2
  or v1.3 as the active schema.
- Legacy schema support remains unproven unless directly evidenced by tests.
