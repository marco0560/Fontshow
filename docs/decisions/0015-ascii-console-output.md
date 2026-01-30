# Decision 0015 - ASCII-only console output

**Date**: 30/01/2026
**Status**: Accepted

## Context

Fontshow emits human-readable messages and diagnostic payloads to the console.
Some environments, log collectors, terminals, or CI pipelines do not reliably
handle non-ASCII characters, leading to:

- garbled output
- broken log parsing
- inconsistent snapshots across platforms

## Decision

Fontshow console output MUST be ASCII-only.

This applies to:

- CLI user-facing messages
- semantic warnings emitted by the pipeline
- normalization diagnostics

## Consequences

- Use `->` instead of Unicode arrows like `→`.
- Avoid non-ASCII symbols (e.g. `ℹ`, `⚠`) in emitted text.
- Structured fields remain unchanged.
- Any future additions to console output must respect this constraint.

## Scope

This decision governs console output only.
It does not constrain internal data structures or JSON payloads.
