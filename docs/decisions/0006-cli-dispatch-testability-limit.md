# Decision 0006 - CLI dispatch testability limitation

## Status

**Status:** Superseded
**Superseded by:** Logging & CLI dispatch refactor (18/01/2026)

## Context

During work on CLI error handling and test refactoring (issues #33, #36, #42),
it emerged that the current CLI architecture binds command handlers via
argparse.set_defaults(func=...), making them non-injectable for end-to-end
CLI tests.

As a result, CLI tests cannot distinguish expected failures (exit code 1)
from internal errors (exit code 2) for some commands (e.g. parse-inventory)
without modifying production code.

## Decision

This decision is no longer valid.

The CLI dispatch mechanism has been refactored so that:

- command handlers are injected via `argparse.set_defaults(func=...)`
- handlers return exit codes instead of calling `sys.exit`
- logging is fully testable
- CLI behavior is deterministic and mockable

The original limitation no longer applies.

## Consequences

- CLI tests now fully exercise command behavior
- Exit codes are deterministic
- Logging is verifiable via `caplog`
- No test-only hacks are required

## References

- Branch: fix/parse-inventory-io-errors
- Issues: #33, #36, #42
