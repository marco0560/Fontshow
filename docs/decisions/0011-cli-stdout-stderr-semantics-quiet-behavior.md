# Decision 0011 - CLI stdout / stderr semantics and `--quiet` behavior

## Status

**Date**: 23/01/2026
**Status**: Accepted

## Context

During the implementation and stabilization of the CLI output behavior for
`fontshow create-catalog`, several inconsistencies emerged between:

- expected CLI behavior
- actual runtime behavior
- test assumptions

In particular, the interaction between:

- `--quiet`
- `--verbose`
- warnings emitted during font processing
- `argparse` error handling

required clarification and formalization.

## Observed Behavior

1. **`argparse` always writes parsing errors to `stderr`**
   - This includes mutually exclusive flags such as `--quiet` and `--verbose`
   - Exit code is non-zero
   - Output is *not* suppressible via `--quiet`

2. **Warnings during font processing**
   - Warnings (e.g. unexpected font entries) are written to `stderr`
   - They are not fatal
   - They are not controlled by `--quiet`

3. **`--quiet` affects only stdout**
   - It suppresses progress messages and informational output
   - It does **not** suppress:
     - warnings
     - errors
     - argparse diagnostics

4. **Fallback behavior is not an error**
   - When `--inventory` points to a missing file:
     - fallback to system font detection occurs
     - execution continues
     - exit code is `0`
     - warnings may be emitted

## Decision

### 1. Semantics of `--quiet`

`--quiet` suppresses:

- informational output on **stdout**

`--quiet` does **not** suppress:

- warnings
- error messages
- argparse diagnostics

This behavior is intentional and aligned with standard UNIX CLI conventions.

---

### 2. stderr is allowed output

The following outputs are valid on `stderr`:

- warnings emitted during font normalization
- fallback notifications
- argument parsing errors
- runtime errors

Tests must not assume `stderr == ""` unless explicitly testing silence.

---

### 3. Tests must reflect real CLI behavior

Tests asserting:

```python
assert result.stderr.strip() == ""
```

are invalid unless:

- the command is expected to be completely silent
- no warnings or argparse errors are possible

Tests must instead:

- assert return code
- assert presence or absence of stdout
- optionally match specific stderr content

---

### 4. Responsibility separation

| Layer            | Responsibility                                |
|------------------|-----------------------------------------------|
| CLI (`argparse`) | Argument validation, usage errors             |
| Core logic       | Processing, fallback behavior                 |
| Logging          | Warnings and diagnostics                      |
| Tests            | Validate observable behavior, not assumptions |

---

## Consequences

- CLI behavior is now clearly defined
- Tests are aligned with real execution
- No hidden coupling between `--quiet` and error handling
- Logging remains consistent and debuggable
- No further changes required in core logic

---

## Follow-up

- Future CLI commands should follow the same stdout/stderr contract
- Tests should avoid asserting empty stderr unless strictly necessary
- This decision applies to all subcommands
