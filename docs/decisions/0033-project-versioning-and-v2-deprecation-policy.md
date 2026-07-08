# Decision 0033 - Project Versioning and v2 Deprecation Policy

**Date**: 08/07/2026
**Status**: Accepted

## Context

Fontshow has several versioned surfaces:

- the Python package version
- command-line behavior
- inventory schema versions
- planning documents for possible v2.x.y architecture work

The current roadmap keeps pluggable font discovery and other v2.x.y
architecture work out of scope for the 0.x series. The v2 design spike is
explicitly non-binding and does not deprecate current v0.x behavior.

Issue #39 requires a stable deprecation policy for v2.x.y features. The
out-of-band planning notes also identify the need to define MAJOR, MINOR, and
PATCH meaning for the project and to clarify the relationship between project
versioning and schema versioning.

## Decision

Fontshow uses the package version to communicate project-level compatibility
and the inventory schema version to communicate persisted data compatibility.
These are related but independent contracts.

### Package Version Policy

- **MAJOR** versions may introduce intentional breaking changes to public
  behavior, CLI contracts, architecture boundaries, or supported platform
  assumptions.
- **MINOR** versions may add features, commands, options, schema fields, or
  documented capabilities while preserving documented compatibility for
  existing supported workflows.
- **PATCH** versions may fix defects, tighten documentation, improve tests,
  or make internal changes that preserve documented public behavior.

During the 0.x series, compatibility is still expected for documented behavior
unless a decision record or release note explicitly says otherwise. The 0.x
prefix does not permit silent breakage.

### Inventory Schema Version Policy

Inventory schema versions are governed by schema files, tests, and schema ADRs.
They must not be inferred from the package version.

Schema changes that alter required fields, accepted values, validation
semantics, or persisted runtime evidence require:

- an updated schema file
- matching tests
- documentation updates
- an ADR or superseding decision when the change affects the durable inventory
  contract

### v2.x.y Deprecation Policy

v2.x.y features are not deprecated merely because they appear in a design
spike, roadmap, issue, or planning note. A v2 feature becomes active project
direction only after a dedicated decision record or approved implementation
plan accepts it.

Deprecating existing v0.x behavior for a v2 path requires:

- identifying the behavior being deprecated
- explaining the replacement or migration path
- documenting the affected commands, schema fields, or runtime assumptions
- adding or updating tests for the transition behavior
- recording the decision in an ADR, release note, or both

The project must not remove or reinterpret existing documented behavior solely
because a v2 alternative is under exploration.

## Consequences

- v2 design work remains exploratory until accepted through the project
  decision process.
- Users and maintainers can distinguish package compatibility from inventory
  schema compatibility.
- Future breaking changes need explicit traceability from issue or ADR to
  tests and documentation.
- Existing v0.x behavior remains protected from accidental deprecation while
  v2.x.y architecture is being explored.
