# Exception Policy — Fontshow

## Purpose

This document defines the **uniform exception semantics** used across the Fontshow codebase.
Its goals are:

- eliminate ambiguity in failure handling
- ensure consistent CLI behavior
- make failure classification explicit
- improve static analyzability and determinism
- remove blind exception handling

This policy applies to **all core modules, CLI wrappers, scripts, and tests**.

---

## Exception Categories

### 1. Controlled CLI Failure → `TypeError`

A `TypeError` represents a **controlled, semantic failure** detected by the pipeline.

Typical causes:

- invalid inventory structure
- schema violation
- invalid CLI semantic state
- pipeline contract violation
- unsupported configuration detected at runtime

#### Rule

```text
TypeError ⇒ controlled CLI failure ⇒ exit code 2
```

All CLI wrappers MUST map `TypeError` to exit code `2`.

Example:

```python
try:
    return _run_command(args)
except TypeError as exc:
    log_err(str(exc))
    return 2
```

---

### 2. Structural / Schema Validation → `ValueError`

`ValueError` represents **invalid structured data**.

Typical causes:

- JSON structure invalid
- schema validation failure
- malformed inventory content
- invalid normalized data

`ValueError` MAY be converted into `TypeError` at CLI boundary when it represents
a user-visible semantic failure.

---

### 3. Operational Failures → Specific Exceptions

Operational failures MUST NOT use `Exception`.

Use the most specific applicable exception:

| Domain             | Exception                    |
|--------------------|------------------------------|
| Filesystem / I/O   | `OSError`                    |
| JSON parsing       | `json.JSONDecodeError`       |
| Subprocess         | `subprocess.SubprocessError` |
| Unicode / decoding | `UnicodeError`               |
| FontTools parsing  | `TTLibError`                 |

These may be:

- handled locally
- converted to `TypeError`
- propagated

---

### 4. Defensive / Best-Effort Blocks

Used when failure MUST NOT stop the pipeline.

Typical locations:

- font metadata extraction
- optional enrichment
- cache loading
- malformed optional font tables

Rules:

- MUST catch **specific operational exceptions**
- MUST NOT use blind `except Exception`
- MUST preserve non-fatal behavior

Example:

```python
try:
    value = optional_operation()
except (OSError, ValueError):
    value = None
```

---

### 5. Programming Errors / Unexpected Bugs

Programming errors MUST NOT be converted into controlled failures.

Examples:

- logic bugs
- invariant violations
- unexpected state

These MUST propagate naturally.

---

### 6. Script Transaction Blocks

Scripts performing filesystem changes may use:

- cleanup
- rollback
- then re-raise

Example:

```python
try:
    perform_operation()
except (OSError, ValueError):
    cleanup()
    raise
```

---

### 7. Test Harness Exception Mapping

Tests sometimes intentionally map unexpected failures to CLI exit codes.

In this context, broad exception handling is allowed **only with explicit justification**.

Example:

```python
except Exception:  # noqa: BLE001
    code = 2
```

---

## CLI Wrapper Contract

Every CLI entrypoint MUST follow:

```python
try:
    exit_code = _run_command(args)
except TypeError as exc:
    log_err(str(exc))
    return 2
```

No other exception should be caught at top level.

---

## Prohibited Patterns

The following are NOT allowed:

- `except Exception:` without justification
- `except Exception: pass`
- useless `except Exception: raise`
- catching broad exceptions in operational code
- unreachable code after `raise`

---

## Summary

| Category               | Exception           | Behavior                 |
|------------------------|---------------------|--------------------------|
| Controlled CLI failure | `TypeError`         | exit code 2              |
| Schema / structural    | `ValueError`        | may convert to TypeError |
| Operational            | specific            | handle or propagate      |
| Defensive              | specific            | non-fatal                |
| Programming bug        | uncaught            | propagate                |
| Script transactional   | specific + re-raise | fail after cleanup       |
| Test harness           | broad (justified)   | controlled mapping       |

---

## Status

Adopted in **v0.36.0 — Ruff cleanup phase 1**.

This policy is **mandatory for all future code**.
