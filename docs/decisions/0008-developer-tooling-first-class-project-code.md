# 0008 - Developer tooling is first-class project code, but outside the public API surface

Date: 16/01/2026
Status: Accepted

## Context

Over time, the Fontshow project has accumulated several developer-facing tools
used to support development workflows, such as:

- repository cleanup helpers
- decision note generators
- release preview helpers
- local testing scripts

Historically, such tools are often treated as ad-hoc scripts, written in
different languages (e.g. Bash), loosely documented, and implicitly excluded
from architectural reasoning.

During recent refactoring and standardization efforts, it became clear that
these tools:

- materially affect developer experience and project reliability
- are routinely used and relied upon by contributors
- benefit from consistent structure, determinism, and documentation

At the same time, these tools are **not** part of Fontshow’s public API and are
not intended for consumption by end users or downstream integrations.

This decision formalizes their status and expectations.

## Decision

Developer tooling in the Fontshow project is treated as **first-class project
code**, while being **explicitly outside the public API surface**.

In practice:

- Developer tools are official parts of the repository
- They are maintained, documented, and subject to quality standards
- They are **not** considered stable public APIs
- They may evolve, be refactored, or be replaced without backward-compatibility
  guarantees

This distinction is intentional and explicit.

## Consequences

### What this means

- Developer tools (e.g. scripts under `scripts/`, git aliases invoking them)
  are:
  - written in Python for portability and consistency
  - deterministic and offline-safe by default
  - documented in project documentation
  - free to depend on project internals if appropriate

- Changes to developer tooling:
  - do not require semantic versioning
  - do not imply breaking changes for users
  - may be made to improve ergonomics or maintainability

- Refactoring or replacing tooling is acceptable as long as:
  - intent and usage are preserved or clearly documented
  - developer workflows are not silently broken

### What this does *not* mean

- Developer tools are **not** part of the public CLI or library API
- No backward-compatibility guarantees are provided for external consumers
- They are not required to maintain long-term stability across releases

## Rationale

This approach balances two competing needs:

- treating developer tooling as disposable scripts leads to fragility,
  inconsistency, and hidden technical debt
- treating developer tooling as public API would impose unnecessary constraints
  and slow down iteration

By making tooling first-class but non-API, the project gains:

- clarity of intent
- freedom to improve workflows
- reduced ambiguity about stability expectations

## Related decisions

- Standardization of project scripts in Python
- CLI contract definition and normalization
- Separation between public CLI surface and internal implementation details

## Notes

This decision applies only to developer-facing tooling and helpers.
It does not affect the stability guarantees of Fontshow’s public CLI commands
or library interfaces.
