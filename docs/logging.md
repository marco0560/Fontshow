# Logging in Fontshow

Fontshow uses a **structured, centralized logging model** designed to be:

- deterministic
- testable
- CLI-friendly
- extensible without side effects

Logging is treated as **part of the public behavior of the tool**, not as
an implementation detail.

---

## 1. Design principles

### 1.1 Single global logger

Fontshow uses **one single logger**:

```python
logging.getLogger("fontshow")
```

This logger is:

- shared by all modules
- configured only once
- never replaced
- never wrapped

There are **no per-module loggers**.

---

### 1.2 No configuration in business code

Modules **must not**:

- add handlers
- set levels
- configure formatters
- call `basicConfig()`

All configuration is centralized in:

```text
src/fontshow/core/logging_utils.py
```

---

### 1.3 Structured logging

All logs use structured payloads:

```python
logger.info(
    "font inventory parsing started",
    extra={
        "schema_version": schema_version,
        "fonts_count": len(fonts),
    },
)
```

Rules:

- Message = human readable
- `extra` = machine readable
- No string formatting inside messages
- No f-strings for log messages

---

## 2. logging_utils.py

The file `src/fontshow/core/logging_utils.py` is the **only place** where logging is configured.

Responsibilities:

- create the `fontshow` logger
- attach a handler (if enabled)
- define formatting policy
- expose helper utilities if needed

It **must not**:

- import application modules
- perform I/O
- depend on CLI arguments

---

## 3. Logger usage in modules

Each module must:

```python
from fontshow.logging_utils import logger
```

And then use:

```python
logger.info(...)
logger.warning(...)
logger.error(...)
```

❌ Do NOT use:

```python
logging.getLogger(__name__)
```

❌ Do NOT create new loggers.

---

## 4. CLI logging behavior

- CLI commands do **not** print directly
- Output is produced only by:
  - logging
  - return codes

This allows:

- test capture via `caplog`
- silent mode
- redirection
- consistent automation

---

## 5. Testing expectations

Tests assume:

- all logs go through `fontshow` logger
- messages are emitted with `logger.<level>()`
- no stdout/stderr pollution
- structured fields are preserved

Example test assertion:

```python
assert "font inventory parsing started" in messages
```

---

## 6. What NOT to do

❌ Do not use:

- `print()`
- `basicConfig()`
- `logging.getLogger(__name__)`
- inline formatting in log strings

❌ Do not configure logging in:

- `__main__.py`
- command modules
- tests

---

## 7. Rationale

This design allows:

- deterministic CLI behavior
- clean testability
- future JSON logging
- centralized formatting
- pluggable output backends

It also avoids the most common Python logging pitfalls.

---

## 8. Summary

✔ One logger
✔ Structured messages
✔ Centralized config
✔ Test-friendly
✔ CLI-safe

This is the **only supported logging model in Fontshow**.
