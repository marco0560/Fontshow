# Decision 0005 — CLI error handling normalization

## Status

**Status:** Accepted
**Date:** 15/01/2026

## Context

Fontshow provides a command-line interface (CLI) intended for:

- interactive usage
- scripting
- CI automation

A formal CLI contract has been defined, specifying:

- exit code semantics
- stdout / stderr separation
- invariants on observable behavior

During an audit of the existing CLI commands, it emerged that:

- most error conditions are currently mapped to exit code `1`
- a limited number of commands already return exit code `2` for internal
  or unexpected errors
- this behavior is not documented and not applied consistently

While this behavior does not break existing usage, it weakens the
semantic value of exit codes and reduces diagnostic precision.

---

## Decision

The CLI error handling is normalized according to the following rules:

1. **Exit code `0`**
   - Successful execution

2. **Exit code `1`**
   - Expected errors, including:
     - invalid user input
     - missing or invalid files
     - schema validation failures
     - unsupported environment conditions

3. **Exit code `2`**
   - Unexpected or internal errors, including:
     - uncaught exceptions
     - programming errors
     - failures of external tools not attributable to user input

This distinction is normative and applies to all CLI commands.

---

## Design constraints

- No change to user-facing messages
- No change to stdout / stderr routing
- No refactor of core business logic
- Normalization must be implemented locally per command
- Behavior must remain deterministic

---

## Scope

In scope:

- CLI wrapper layers
- mapping of exceptions to exit codes

Out of scope:

- changes to logging behavior
- new exception hierarchies
- changes to command semantics
- retries or recovery logic

---

## Rationale

Distinguishing expected from internal errors:

- improves scriptability and CI integration
- preserves backward compatibility
- aligns implementation with the documented CLI contract
- enables future test coverage of error paths

---

## Consequences

- Existing scripts relying on exit code `1` for all failures continue to work
- Internal failures become explicitly detectable via exit code `2`
- Future CLI commands must follow this rule by default
