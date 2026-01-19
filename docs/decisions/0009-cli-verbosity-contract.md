# 0009 – CLI verbosity contract

Date: 2026-01-19
Status: Accepted

## Context

Fontshow provides multiple CLI commands intended to be used both:

- interactively by humans
- programmatically (scripts, CI, tooling)

Several commands already expose the flags `--quiet` and `--verbose`,
but their behavior has historically been inconsistent and only partially
implemented.

This led to ambiguity about:

- what output is expected in each mode
- how commands should behave in scripting contexts
- how much output is acceptable by default

A clear and uniform contract is required to ensure consistency,
testability, and long-term maintainability.

---

## Decision

The following **verbosity contract** is established for all Fontshow CLI commands.

### 1. `--quiet`

- Suppresses all non-essential output
- Produces **no stdout output**
- Only errors may be emitted on stderr
- The command communicates success or failure **only via exit code**

This mode is intended for:

- scripting
- CI usage
- automation

---

### 2. Default mode (no verbosity flags)

- Produces minimal, human-readable output
- Typically a **single completion message**
- No diagnostic or debug information
- No structured or verbose logs

This is the standard interactive mode.

---

### 3. `--verbose`

- Enables additional informational output
- May include:
  - diagnostic messages
  - processing details
  - intermediate steps
- Must not change functional behavior
- Must not be required for correct execution

This mode is intended for:

- debugging
- development
- inspection of internal processing

---

## Scope

This contract applies to:

- all CLI commands
- all current and future subcommands
- both direct execution and dispatcher-based invocation

---

## Non-goals

- Introducing logging frameworks
- Changing functional behavior of commands
- Enforcing a specific output format
- Retrofitting historical scripts

---

## Consequences

### Positive

- Predictable CLI behavior
- Clear separation between human and machine usage
- Simplified testing
- Easier future automation

### Trade-offs

- Requires minor refactoring of existing commands
- Some legacy output will need to be adjusted

---

## Notes

This decision defines **behavioral intent**, not implementation details.

Actual enforcement is performed incrementally and tracked via
dedicated issues.

## Related issues

- #46 — CLI stdout/stderr audit and classification
