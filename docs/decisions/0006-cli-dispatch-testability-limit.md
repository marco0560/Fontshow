# 0006 - CLI dispatch testability limitation

## Status

**Status:** Accepted
**Date:** 16/01/2026

## Context

During work on CLI error handling and test refactoring (issues #33, #36, #42),
it emerged that the current CLI architecture binds command handlers via
argparse.set_defaults(func=...), making them non-injectable for end-to-end
CLI tests.

As a result, CLI tests cannot distinguish expected failures (exit code 1)
from internal errors (exit code 2) for some commands (e.g. parse-inventory)
without modifying production code.

## Decision

The limitation is accepted for now.
CLI tests are aligned to the current architecture and explicitly document
this behavior.

## Consequences

- CLI tests remain slightly less expressive than desired
- No workaround or test-only hacks are introduced
- A future refactor of CLI dispatch may address this limitation

## References

- Branch: fix/parse-inventory-io-errors
- Issues: #33, #36, #42
