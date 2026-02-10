# Developer Guide — TRACE Logging

## 1. Purpose

TRACE is Fontshow’s **structured observability layer**.

It provides:

- Deep execution visibility
- Deterministic diagnostics
- Machine-readable introspection
- Performance tracing
- Inference reasoning transparency

TRACE is **not** for user messages and **not** a replacement for errors/warnings.

---

## 2. When to Use TRACE

Use TRACE when you need to record:

### Execution Flow (`flow`)

- Entry/exit of major functions
- Stage lifecycle
- CLI dispatch
- Pipeline boundaries

### External Interactions (`io`)

- Subprocess calls
- Filesystem probing
- External tools (`fc-query`, `fc-list`, fonttools)

### Raw Data (`raw`)

- Raw external outputs (bounded)
- Formatting decisions
- Intermediate data representations

### Parsing (`parse`)

- Normalization steps
- Filtering decisions
- Transformation stages

### Inference (`infer`)

- Decision reasoning
- Candidate acceptance/rejection
- Evidence and confidence

### Validation (`validate`)

- Schema rule failures
- Semantic rule triggers
- Strict-mode rejection

### Cache (`cache`)

- Cache hit/miss/store

### Performance (`perf`)

- Timing spans
- Performance metrics

### LaTeX (`latex`)

- Layout decisions
- Formatting steps
- Output shaping

---

## 3. When NOT to Use TRACE

Do NOT use TRACE for:

- User-visible messages → use INFO/WARN/ERROR
- Errors/exceptions → use ERROR
- Debug print-style logging → DEBUG (temporary only)
- Summaries → INFO
- Results → INFO

---

## 4. TRACE Logging API

Always use:

```python
log_trace_cat(log, "<category>", "<message>", extra={...})
```

Example:

```python
log_trace_cat(
    log,
    "infer",
    "language candidate accepted",
    extra={
        "lang": lang,
        "confidence": confidence,
        "evidence_count": len(evidence),
    },
)
```

---

## 5. TRACE Field Naming Standard

TRACE payload fields MUST follow **stable naming conventions**.

### General rules

- Use **snake_case**
- Use **deterministic values**
- Prefer **explicit names**
- Keep payload **bounded**
- Avoid ambiguity

---

### Standard Field Names

#### Execution / flow

| Field       | Meaning            |
|-------------|--------------------|
| `stage`     | logical stage name |
| `command`   | CLI command        |
| `handler`   | resolved function  |
| `exit_code` | process exit code  |

---

#### Paths / filesystem

| Field         | Meaning        |
|---------------|----------------|
| `font_path`   | font file path |
| `input_path`  | input file     |
| `output_path` | output file    |

---

#### Counts / sizes

| Field          | Meaning        |
|----------------|----------------|
| `count`        | generic count  |
| `fonts_total`  | total fonts    |
| `fonts_parsed` | parsed fonts   |
| `faces`        | TTC face count |
| `bytes`        | byte size      |

---

#### Inference

| Field        | Meaning              |
|--------------|----------------------|
| `lang`       | language code        |
| `confidence` | inference confidence |
| `evidence`   | inference evidence   |
| `ratio`      | coverage ratio       |
| `threshold`  | inference threshold  |

---

#### Validation

| Field            | Meaning         |
|------------------|-----------------|
| `rule`           | rule identifier |
| `severity`       | warning/error   |
| `schema_version` | schema version  |

---

#### External calls

| Field         | Meaning          |
|---------------|------------------|
| `command`     | external command |
| `duration_ms` | execution time   |
| `exit_code`   | return code      |

---

#### Cache

| Field       | Meaning   |
|-------------|-----------|
| `cache_key` | cache key |
| `hit`       | bool      |
| `store`     | bool      |

---

## 6. TRACE Performance Checklist

TRACE must remain **cheap when disabled**.

### Always verify

- TRACE produces **no side effects**
- TRACE does **not change output**
- TRACE does **not alter ordering**
- TRACE does **not allocate large payloads**
- TRACE does **not compute heavy values unnecessarily**

---

### Guard heavy TRACE

```python
if log.isEnabledFor(TRACE) and trace_enabled("raw"):
    expensive_data = compute()
```

---

### Timing best practices

- Use `perf_counter()`
- Convert to `duration_ms`
- Avoid timing inside tight loops unless aggregated

---

### Hot-loop rules

Allowed:

- aggregated TRACE
- gated TRACE

Avoid:

- TRACE per iteration in large loops
- TRACE with large payloads

---

## 7. Determinism Guarantee

TRACE must **never change**:

- Program output
- File content
- Ordering
- Exit codes
- Logic

TRACE is strictly observational.

---

## 8. TRACE Categories

Fixed authoritative categories:

```text
flow io raw parse infer validate cache perf latex
```

Never introduce new categories without updating the TRACE policy.

---

## 9. Caller Reporting

TRACE must reflect the **logical caller**, not logging helpers.

Use:

```python
stacklevel=2
```

when needed.

---

## 10. TRACE Instrumentation Cheat Sheet

### Stage entry / exit

```python
log_trace_cat(log, "flow", "stage started")
...
log_trace_cat(log, "flow", "stage completed")
```

---

### External command

```python
log_trace_cat(log, "io", "fc-query start", extra={"font_path": path})
...
log_trace_cat(log, "io", "fc-query executed", extra={"exit_code": rc})
```

---

### Performance timing

```python
t0 = perf_counter()
...
log_trace_cat(log, "perf", "operation timing", extra={"duration_ms": ms})
```

---

### Cache hit / miss

```python
log_trace_cat(log, "cache", "cache hit", extra={"cache_key": key})
log_trace_cat(log, "cache", "cache miss", extra={"cache_key": key})
```

---

### Inference decision

```python
log_trace_cat(
    log,
    "infer",
    "candidate rejected",
    extra={"lang": lang, "ratio": ratio},
)
```

---

### Validation rule

```python
log_trace_cat(
    log,
    "validate",
    "rule triggered",
    extra={"rule": rule_id, "severity": severity},
)
```

---

### Raw bounded data

```python
log_trace_cat(
    log,
    "raw",
    "raw output",
    extra={"raw": blob[:4096]},
)
```

---

## 11. TRACE Activation (Developer)

Enable TRACE:

```bash
FONTSHOW_LOG_LEVEL=TRACE
```

Selective categories:

```bash
FONTSHOW_TRACE=flow,io,infer
```

Human-readable format:

```bash
FONTSHOW_TRACE_FORMAT=human
```

---

## 12. Common Mistakes

- Using TRACE for user messages ❌
- Creating new categories ❌
- Logging inside hot loops without gating ❌
- Logging large raw data without bounding ❌
- Computing heavy TRACE data unconditionally ❌

---

## 13. TRACE Philosophy

TRACE is:

- Structured
- Deterministic
- Selectively activatable
- Performance-safe
- Observational only

It enables **deep introspection without altering runtime behavior**.
