# Decision 0018 - TRACE Logging Architecture & Semantics

**Date**: 08/02/2026
**Status**: Accepted
**Scope**: Logging / Observability / Diagnostics
**Applies to**: Entire Fontshow codebase

## 1. Purpose

TRACE is the **lowest-level observability channel** in Fontshow.

It is intended for:

- execution tracing
- raw data inspection
- parsing pipeline diagnostics
- inference reasoning
- internal state transitions

TRACE **must not** be used for user diagnostics, warnings, or standard debugging output.

---

## 2. TRACE Semantic Contract

### TRACE MUST be used for

- external interactions (subprocess / filesystem / tools)
- raw external outputs (bounded)
- parsing pipeline steps
- internal decision paths (not results)
- cache behavior
- inference reasoning

### TRACE MUST NOT be used for

- user-visible diagnostics
- warnings/errors
- normal DEBUG logging
- formatted summaries

---

## 3. TRACE Categories

TRACE is divided into **selectively activatable categories**:

| Category   | Meaning                                                            |
|------------|--------------------------------------------------------------------|
| `io`       | External interaction (subprocess, OS, filesystem probing)          |
| `raw`      | Raw external data (stdout blobs, raw fc-query, etc.)               |
| `parse`    | Parsing pipeline internal steps                                    |
| `infer`    | Script/language inference reasoning                                |
| `validate` | Schema/semantic validation decisions                               |
| `cache`    | Cache hit/miss and persistence                                     |
| `perf`     | Optional timing / performance micro-metrics                        |
| `flow`     | Execution flow, pipeline/stage boundaries, orchestration lifecycle |
| `latex`    | LaTeX generation, formatting, and layout decisions                 |

Categories are **closed and stable identifiers** used both in code and configuration.
No dynamic categories are allowed.

---

## 4. TRACE Activation Model

TRACE emission requires **two conditions**:

1. Global log level allows TRACE
2. TRACE category is enabled

### 4.1 Global Level

```bash
FONTSHOW_LOG_LEVEL=TRACE
```

If TRACE level is not active, **no TRACE is emitted** regardless of category settings.

---

### 4.2 Category Selector

Environment variable:

```text
FONTSHOW_TRACE
```

Syntax:

- `all` → enable all categories
- `none` → disable all TRACE
- `cat1,cat2` → enable only listed categories
- `-cat` → exclude category
- `cat1,cat2,-cat3` → mixed include/exclude

Defaults:

- If TRACE level active and selector unset → behaves as `all`
- If TRACE level inactive → selector ignored

Unknown categories are ignored.

Examples:

```bash
FONTSHOW_LOG_LEVEL=TRACE FONTSHOW_TRACE=all
FONTSHOW_LOG_LEVEL=TRACE FONTSHOW_TRACE=io,parse
FONTSHOW_LOG_LEVEL=TRACE FONTSHOW_TRACE=infer,-raw
FONTSHOW_LOG_LEVEL=TRACE FONTSHOW_TRACE=none
```

---

## 5. Inference Debugging

The legacy variable:

```bash
FONTSHOW_DEBUG_INFERENCE
```

**has been removed.**

Inference diagnostics are now emitted exclusively through:

```text
TRACE category: infer
```

Example:

```bash
FONTSHOW_LOG_LEVEL=TRACE FONTSHOW_TRACE=infer fontshow parse-inventory
```

---

## 6. Structured TRACE Output

All TRACE events are structured and include:

```python
extra["trace_category"] = "<category>"
```

This allows:

- machine filtering
- testing
- post-processing
- future trace exporters

TRACE payload MUST:

- use snake_case field names
- remain deterministic
- avoid unbounded data

---

## 7. Human-Readable TRACE Rendering

By default, TRACE is structured and optimized for machine consumption.

To force human-readable rendering:

```bash
FONTSHOW_TRACE_FORMAT=human
```

Behavior:

- Formats TRACE messages in readable text form
- Includes `trace_category`
- Includes selected `extra` fields
- Preserves existing log formatting style

If unset or set to `json` (default), structured TRACE is emitted.

---

## 8. RAW Category Guardrails

The `raw` category may produce large outputs.

To prevent uncontrolled log volume:

```bash
FONTSHOW_TRACE_RAW_MAXLEN=4096
```

Behavior:

- Raw blobs exceeding limit are truncated
- Additional metadata added:

```text
raw_truncated: true
raw_len: <original_length>
```

---

## 9. Caller Identity Rule

TRACE must report the **first semantic execution owner**, not logging helpers.

Allowed:

- functional helpers representing real execution boundary
  e.g. `_run_fc_query`

Not allowed:

- logging wrappers or infrastructure functions

---

## 10. Performance Contract

When TRACE is **disabled**:

- overhead MUST be negligible
- no expensive computation for TRACE-only values
- no large payload allocation

When TRACE is **enabled**:

- timing uses lightweight `perf_counter`
- hot loops MUST gate or aggregate TRACE
- TRACE MUST NOT change program behavior

---

## 11. DEBUG Decommission

DEBUG is no longer the primary observability channel.

- TRACE is the canonical structured observability layer
- DEBUG may remain for temporary developer-only probes
- No new structured diagnostics should be added to DEBUG

---

## 12. Stability Guarantees

This TRACE architecture:

- does NOT change CLI behavior
- does NOT affect exit codes
- does NOT emit TRACE unless explicitly enabled
- preserves existing DEBUG / INFO / WARN semantics
- has negligible overhead when disabled
- does not affect determinism or ordering

---

## 13. Observability Coverage Goals

TRACE SHOULD cover:

- execution lifecycle (`flow`)
- external calls (`io`)
- cache behavior (`cache`)
- inference evidence (`infer`)
- validation rules (`validate`)
- timing metrics (`perf`)
- formatting and generation (`raw`, `latex`)

Coverage MUST remain stable across releases.

---

## 14. Future Extensions (Non-binding)

Potential evolutions:

- selective TRACE exporters (file, JSONL, analysis tools)
- category-specific rate limiting
- per-module TRACE filters
- structured inference trace viewer
- performance tracing mode

These are outside current scope.

---

## 15. Summary

TRACE is now:

- structured
- category-selective
- inference-aware
- human-renderable
- stable and deterministic
- suitable for deep observability without affecting runtime behavior

---
