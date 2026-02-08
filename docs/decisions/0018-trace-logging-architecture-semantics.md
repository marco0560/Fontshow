# Decision 0018 - TRACE Logging Architecture & Semantics

**Date**: 08/02/2026
**Status**: Accepted
**Scope**: Logging / Observability / Diagnostics
**Applies to**: Entire Fontshow codebase

## 1. Context

Fontshow emits three categories of logs:

- **User layer**: user-facing CLI output (`log_ok`, `log_info`, `log_warn`, `log_err`)
- **Developer layer**: DEBUG-level diagnostics
- **Trace layer**: TRACE-level execution tracing

TRACE semantics were previously only partially specified and some tests implicitly relied on a strict interpretation of “public caller attribution”. Recent refactoring introduced functional helpers that represent real execution boundaries, which must remain visible in TRACE without reverting to logging-helper attribution.

## 2. Goals

This decision establishes a stable observability contract:

- Deterministic behavior
- Clear separation of User vs DEBUG vs TRACE
- Caller attribution rules that avoid logging-helper noise
- Structured fields for machine-readable diagnostics
- Test contract that is robust to refactors
- Near-zero overhead when TRACE is disabled

## 3. Logging layers

### 3.1 User layer (CLI contract)

User-facing messages:

- MUST respect `--quiet`
- MUST preserve established CLI semantics and wording where contractually specified
- MUST NOT leak internal debug information
- SHOULD remain human-readable and actionable

This layer is the stable “public contract”.

### 3.2 DEBUG layer (semantic diagnostics)

DEBUG logs are for developers and maintainers:

- SHOULD report semantic state and decisions
- SHOULD remain deterministic
- SHOULD include structured fields in `extra` where applicable
- MUST NOT depend on the ordering of unrelated logs for correctness

Examples:

- validation summaries
- normalization outcomes
- inference summaries
- extracted metadata counts

### 3.3 TRACE layer (execution flow)

TRACE logs are for deep debugging of execution flow:

- SHOULD report operational events and mechanisms
- SHOULD include structured fields in `extra` where applicable
- MUST avoid expensive formatting when TRACE is disabled

Examples:

- subprocess execution and exit codes
- raw external tool output receipt
- branch/fallback activation
- parsing stages at a mechanical level

### 3.4 — Activating logging levels

Fontshow logging is controlled through the environment variable `FONTSHOW_LOG_LEVEL`.
Accepted values (case-insensitive) are:

- `ERROR` → only fatal errors
- `WARN`  → warnings and errors
- `INFO`  → user-level informational messages (default)
- `DEBUG` → developer diagnostics (semantic state, validation, inference)
- `TRACE` → deep execution tracing (subprocess calls, parsing flow, raw inputs)

Examples:

```bash
# Enable DEBUG diagnostics
export FONTSHOW_LOG_LEVEL=DEBUG
fontshow create-catalog

# Enable full TRACE execution tracing
export FONTSHOW_LOG_LEVEL=TRACE
fontshow dump-fonts

# One-shot activation
FONTSHOW_LOG_LEVEL=TRACE fontshow parse-inventory
```

Notes:

- `--quiet` suppresses **user-layer output only** and does **not** disable DEBUG/TRACE logs.
- TRACE may generate large volumes of output and should be used only for debugging.
- When TRACE is disabled, its overhead is negligible by design.

#### Inference-specific debug tracing

Language and script inference can be inspected independently of the global
logging level through the environment variable:

```bash
FONTSHOW_DEBUG_INFERENCE=1
```

When enabled, Fontshow emits a structured diagnostic dump for each processed
font, including:

- Raw Unicode blocks and counts
- Inferred scripts (raw and normalized)
- Candidate languages with scoring details
- Script–language compatibility checks
- Final language ordering decision

Examples:

```bash
# Enable inference diagnostics only
export FONTSHOW_DEBUG_INFERENCE=1
fontshow parse-inventory

# Combine with DEBUG logging
FONTSHOW_LOG_LEVEL=DEBUG FONTSHOW_DEBUG_INFERENCE=1 \
    fontshow parse-inventory

# Full deep inspection
FONTSHOW_LOG_LEVEL=TRACE FONTSHOW_DEBUG_INFERENCE=1 \
    fontshow parse-inventory
```

Notes:

- Inference debug is **orthogonal** to the logging level and can be enabled
  independently.
- Output is intended for developer diagnostics and may be verbose.
- This facility is stable but subject to future restructuring (see TRACE policy).

## 4. Caller attribution rules

TRACE MUST avoid reporting logging helper internals as the caller.

Caller classes:

- **Public functions** (user-facing or module-level API): MUST be allowed as TRACE callers.
- **Functional helpers** (internal helpers that represent real execution layers): MUST be allowed as TRACE callers.
- **Logging helpers / wrappers** (infrastructure that forwards logs): MUST NOT appear as TRACE callers.

Rationale:

- Functional helpers are meaningful execution boundaries.
- Logging wrappers are infrastructure noise and harm trace usefulness.

## 5. DEBUG vs TRACE boundary

DEBUG and TRACE have different responsibilities:

- DEBUG: semantic state and outcomes (what was decided / derived)
- TRACE: execution flow and mechanisms (what happened / how it happened)

Both layers MUST remain deterministic.

## 6. Structured logging schema

For DEBUG and TRACE events, logs SHOULD use:

- `message: str`
- `extra: dict[str, Any]`

Recommended stable keys (where applicable):

- `font_path`
- `family`
- `style`
- `exit_code`
- `stderr`
- `ranges_count`
- `blocks_count`
- `scripts_count`
- `languages_count`
- `infer_level`
- `fields_detected`

Purpose:

- consistent diagnostics
- future structured logging mode
- robust test assertions based on keys rather than wording

## 7. Performance constraints

TRACE MUST be near-zero overhead when disabled:

- SHOULD avoid building large strings or large `extra` payloads unless TRACE is enabled
- SHOULD avoid expensive dumps (`pprint`, large blob formatting) unless explicitly gated
- SHOULD avoid decoding/normalization work solely for logging

## 8. Test contract

Tests MAY assert:

- log level (DEBUG vs TRACE)
- caller module and/or function name, subject to Section 4
- presence of structured keys in `extra`

Tests MUST NOT assert:

- exact message strings (wording and punctuation)
- formatting details
- ordering of unrelated log messages

## 9. Future extensions (non-binding)

Potential extensions enabled by this architecture:

- structured JSON log output mode
- selective trace channels (e.g., `FONTSHOW_TRACE=fc,charset,inference`)
- log sampling / throttling for large inventories
- persistent diagnostic artifacts for offline inspection

These are explicitly out of scope for this decision.

## 10. Consequences

- TRACE semantics are stabilized around execution boundaries, not wrapper internals.
- Functional helper refactors remain traceable without invalidating observability intent.
- Tests can validate observability without becoming brittle.
- The codebase is prepared for future structured logging improvements.
