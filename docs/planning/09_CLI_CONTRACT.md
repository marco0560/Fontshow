# CLI_CONTRACT.md

## Fontshow — Command Line Interface Contract

**Current version:** v0.28.7.post14
**Applies to:** All CLI commands and entry points

---

## Purpose

This document defines the **behavioral contract** of the Fontshow
Command Line Interface (CLI).

It specifies:
- exit code semantics,
- error handling guarantees,
- output expectations,
- and backward compatibility rules.

This document is **normative**.

---

## Scope

This contract applies to:

- `fontshow` CLI entry point,
- `python -m fontshow` invocation,
- all subcommands and flags.

It does not define:
- internal implementation details,
- performance guarantees,
- future feature expansions.

---

## General CLI Principles

- The CLI is a **stable interface**.
- Behavior must be **predictable and documented**.
- Errors must be **explicit and machine-detectable**.
- Silent failure is not acceptable.

---

## Exit Code Semantics

Exit codes MUST follow these rules:

| Exit Code | Meaning                                  |
|----------:|-------------------------------------------|
| 0         | Successful execution                      |
| 1         | Expected failure (user error, validation) |
| 2         | Environment or dependency failure         |
| >2        | Reserved (must be documented if used)     |

Rules:
- Exit codes MUST be consistent across environments.
- A command MUST NOT return `0` if the requested operation failed.

---

## Error Handling

### User Errors

Examples:
- Invalid arguments
- Missing required input
- Invalid configuration

Behavior:
- Exit code `1`
- Clear, human-readable error message
- No stack trace by default

---

### Environment Errors

Examples:
- Missing external tools
- Missing fonts
- LaTeX not available

Behavior:
- Exit code `2`
- Clear explanation of the missing capability
- Guidance on remediation when possible

---

## Output Semantics

### Human-Readable Output

- Default CLI output is human-oriented.
- Messages SHOULD be concise and structured.
- Progress or informational output MAY be suppressed in quiet modes.

---

### Machine-Readable Output

If machine-readable modes are supported:

- They MUST be explicitly requested.
- Output format MUST be documented.
- Output MUST be stable and parseable.

Mixing human-readable and machine-readable output is not allowed.

---

## Quiet and CI Modes

- Quiet modes MUST suppress non-essential output.
- Quiet mode MUST NOT suppress errors.
- CI usage MUST rely on exit codes, not output parsing.

---

## Backward Compatibility

- Changes to CLI behavior MUST be backward compatible
  or explicitly documented as breaking.
- Breaking changes require:
  - documentation,
  - migration guidance,
  - explicit version signaling.

---

## Testing Requirements

- CLI behavior MUST be covered by automated tests.
- Tests MUST validate:
  - exit codes,
  - essential output behavior,
  - error scenarios.

Environment-dependent behavior MUST be isolated and clearly marked.

---

## Status

This CLI contract is **active** and governs all CLI b
