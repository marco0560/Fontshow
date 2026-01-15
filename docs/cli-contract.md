# Fontshow CLI Contract

This document defines the normative contract for the Fontshow command-line
interface (CLI). It specifies observable behavior and guarantees provided
to users, scripts, and automation.

This document is intentionally conservative: it formalizes existing
behavior without introducing new features or breaking changes.

---

## Scope and guarantees

[DECISION]
The Fontshow CLI provides a stable interface intended for:

- interactive use
- scripting
- CI automation

Behavior described in this document is considered part of the public
contract unless explicitly marked otherwise.

---

## Invocation model

[FACT]
Each CLI command is implemented using a layered structure:

- a core function performing business logic
- a thin CLI wrapper responsible for argument parsing and exit handling

[DECISION]
Core functions MUST:

- return an integer exit code
- never call `sys.exit()`
- never print user-facing messages directly

CLI wrappers are responsible for:

- calling the core function
- handling `sys.exit(exit_code)`
- routing messages to stdout or stderr

---

## Exit codes

[FACT]
Exit codes are integers returned by core functions and propagated
unchanged by the CLI wrapper.

[DECISION]
The following exit code conventions are fixed:

| Code | Meaning                          |
|------|----------------------------------|
| 0    | Successful execution             |
| 1    | Expected error (user/input/data) |
| ≥2   | Internal or unexpected error     |

No other semantic meaning is assigned at this time.

---

## Standard output (stdout)

[FACT]
Stdout is currently used to emit:

- command results
- structured data (e.g. JSON output)
- informational messages on success

[DECISION]
Stdout MUST:

- contain only meaningful command output
- be suitable for machine consumption when applicable
- NOT contain error diagnostics

---

## Standard error (stderr)

[FACT]
Error messages are emitted to stderr.

[DECISION]
Stderr MUST be used exclusively for:

- error diagnostics
- user-facing error explanations
- warnings (when applicable)

Stderr output is NOT guaranteed to be machine-readable.

---

## Error categories

[FACT]
Errors can originate from:

- invalid user input
- filesystem or environment conditions
- internal processing failures

[DECISION]
Errors are classified conceptually as:

1. Expected errors (exit code 1)
2. Unexpected/internal errors (exit code ≥2)

This classification is informational and may be refined in future versions.

---

## Invariants

[DECISION]
The following invariants are guaranteed:

- No command prints to stdout on failure.
- Exit codes are deterministic for the same inputs.
- CLI output does not depend on logging configuration.

---

## Non-goals

[DECISION]
This document does NOT:

- define logging formats
- specify localization/i18n behavior
- guarantee backward compatibility for undocumented behavior
- define a stable internal Python API
