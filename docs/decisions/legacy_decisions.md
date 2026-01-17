# Project Decisions (Reverse-Chronological)

This document records the **active and historical technical decisions**
taken during the development of **Fontshow**.

Decisions are listed in **reverse chronological order**:

- the **most recent decisions appear first**;
- older decisions follow below.

This makes the document easier to read as a *current state description*,
while still preserving rationale and context.

All decisions in this file are considered **binding** unless explicitly superseded.

Any changes to these decisions must be:

- explicitly discussed;
- reflected in this document;
- traceable through dedicated commits.

## Logging specification status

This document contains both implemented and forward-looking design
decisions.

In particular, several sections describe **logging behavior and
diagnostic messages that are not yet implemented** in the current
codebase.

This is intentional.

The project follows a design-first approach where logging semantics
and observability goals may be specified ahead of implementation.

### Status conventions

Each logging-related section in this document may declare one of the
following statuses:

- **IMPLEMENTED**
  The described behavior is fully implemented in the current codebase.

- **PLANNED**
  The behavior is specified but not yet implemented.

- **DEFERRED**
  The behavior is intentionally postponed or out of current scope.

Unless explicitly stated, logging specifications MUST NOT be assumed
to be implemented.

### Issue tracking

When applicable, a section may reference a GitHub issue using:

```text
Tracked by: #<issue-number>
```

This indicates that the section is intentionally tracked for future
implementation or revision.

---

## Pipeline idempotency and output behavior

The Fontshow pipeline is designed to be **safe to re-run** by construction.

This does **not** imply strict idempotence in the mathematical sense
(i.e. producing identical output files on every execution), but rather:

- existing outputs are never modified or invalidated,
- repeated executions do not corrupt or depend on previous runs,
- side effects are limited to the creation of new artifacts,
- execution order does not affect correctness.

### dump-fonts

The `dump-fonts` step always writes a single inventory file.

Re-running the command overwrites the target file deterministically.
This behavior is intentional and considered idempotent.

### parse-inventory

This step performs a pure transformation of the input inventory.

It has no side effects and produces deterministic output given the same input.

### create-catalog

The `create-catalog` step intentionally generates **new output files**
using unique filenames.

This design avoids accidental overwrites and allows multiple catalog
generations to coexist.

As a result:

- re-running the command is safe,
- existing outputs are never modified,
- idempotency is guaranteed at the pipeline level, not at the file level.

This behavior is intentional and must not be interpreted as a defect.

## D37 - Decision: Language inference operates strictly on coverage-level data

**Status**: IMPLEMENTED

### Context

During the refinement of language inference thresholds, it was clarified that
`infer_languages()` is a *coverage-level* function and must not depend on:

- font discovery,
- filesystem paths,
- FontConfig,
- or other pipeline-stage heuristics.

The function operates exclusively on Unicode coverage metadata as produced by
the inventory pipeline (i.e. `font_entry["coverage"]`).

### Decision

- `infer_languages()` SHALL accept and evaluate only coverage-level data.
- Tests for language inference SHALL pass a `coverage` dictionary directly.
- Tests SHALL NOT rely on real fonts, system-installed fonts, or filesystem
  paths.
- Threshold-based inference SHALL remain conservative by default to avoid
  false positives on pan-Unicode or utility fonts.

### Rationale

This separation ensures that:

- language inference logic remains deterministic and testable in isolation,
- tests are environment-independent and reproducible,
- pipeline stages retain clear and stable responsibilities.

Any future refinement (e.g. per-block thresholds or charset-derived evidence)
must preserve this separation of concerns.

### Consequences

- Language inference tests were rewritten to operate exclusively on coverage
  dictionaries.
- No changes to the production logic of `infer_languages()` were required.
- Pipeline-level heuristics (font eligibility, discovery, diagnostics) remain
  out of scope for language inference unit tests.

## D36 - Decision: Refine language inference using a global Unicode block coverage threshold

**Status**: IMPLEMENTED
**Notes**: Some refinements explicitly deferred

### D36 - Context

Fontshow infers supported languages based on Unicode coverage information
derived from fontTools analysis and (optionally) Fontconfig charset data.

The previous inference model was presence-based: the mere presence of
codepoints belonging to a Unicode block associated with a language could
trigger language inference.

This approach led to false positives, where a language was inferred based
on a very small number of incidental or symbolic glyphs.

### D36 - Decision

Language inference is refined by introducing a **global coverage threshold**
applied at the Unicode block level.

A language is inferred only if the font covers a **significant percentage**
of at least one Unicode block associated with that language.

The threshold is global and uniform across all blocks and languages.

### Formal rule

Let:

- `B` be a Unicode block associated with language `L`
- `covered(B)` be the number of codepoints from `B` present in the font
- `size(B)` be the total number of codepoints in `B`
- `THRESHOLD` be a global constant

Then:

```text
L is inferred ⇔ ∃ B such that covered(B) / size(B) ≥ THRESHOLD
```

### Initial threshold

```text
LANGUAGE_BLOCK_COVERAGE_THRESHOLD = 0.40
```

This value is intentionally conservative and may be adjusted based on
real-world font analysis.

### D36 - Rationale

- Prevents language inference based on symbolic or accidental glyphs
- Aligns `languages` with functional, text-level usability
- Preserves all coverage facts while refining semantic claims
- Keeps inference deterministic, explainable, and testable

### D36 - Consequences

- Language lists become shorter but more meaningful
- Languages such as Greek (`el`) are no longer inferred from a handful of
  isolated codepoints
- Coverage data remains fully available for advanced analysis and diagnostics

### D36 -  Future evolution

If systematic false negatives are observed, this global threshold may be
replaced or refined by:

- per-script thresholds
- per-block thresholds
- hybrid script + block strategies

Such changes will be introduced only as explicit, documented decisions.

### D36 -  Status

Accepted.

## D35 - Decision: Decode Fontconfig charset bitmap into Unicode ranges (C-Step 5.1)

**Status**: PLANNED
**Tracked by**: #27, #29

### D35 - Context

Fontshow preserves raw Fontconfig charset data as a multiline bitmap
(`coverage.charset.raw`) when available.

This bitmap encodes glyph coverage information but cannot be directly
consumed by downstream enrichment steps without decoding.

### D35 - Decision

A dedicated C-Step (C-Step 5.1) is introduced to decode the Fontconfig
charset bitmap into explicit Unicode ranges.

Whenever `coverage.charset.raw` is present in the inventory, the bitmap
is automatically decoded and the resulting ranges are stored in
`coverage.charset.ranges`.

Decoding is implicit and unconditional; no opt-in flags or CLI switches
are introduced.

### D35 - Rationale

- Charset bitmap decoding is a pure normalization step.
- Automatic decoding avoids divergent inventory states.
- Downstream enrichment requires explicit Unicode ranges.

### D35 -  Constraints

- Decoding is best-effort and must not abort the pipeline.
- Malformed bitmap lines must be skipped with structured warnings.
- No semantic precedence between charset-derived and fontTools-derived
  coverage is defined at this stage.

### D35 - Consequences

- Charset-derived enrichment becomes technically possible.
- Additional C-Steps are required to define how charset-derived coverage
  interacts with other coverage sources.

### D35 -  Example

Before decoding:

```json
"charset": {
  "raw": "<bitmap>",
  "ranges": []
}
```

After decoding:

```json
"charset": {
  "raw": "<bitmap>",
  "ranges": [[start, end], ...]
}
```

### D35 - Status

Accepted — implementation scheduled as C-Step 5.1.

## D34 - Decision: TRACE logging semantics and testing strategy

**Status**: PLANNED
**Tracked by**: #26, #29

### D34 - Context

Fontshow introduces a custom `TRACE` logging level to support deep, high-volume introspection
(e.g. per-font execution paths during large inventory dumps).
Given the potentially massive number of emitted events, it is essential to clearly separate
`DEBUG` and `TRACE` semantics.

### D34 - Decision

- `TRACE` is defined as a *strictly opt-in* verbosity level.
- When `FONTSHOW_LOG_LEVEL=DEBUG`, `TRACE` messages **must not** be emitted.
- When `FONTSHOW_LOG_LEVEL=TRACE`, both `DEBUG` and `TRACE` messages are emitted.
- The implementation relies on standard `logging.Logger.isEnabledFor()` semantics.
- No custom filtering logic is added beyond correct logger/handler level configuration.

### Caller attribution

- All `TRACE` records must report the *real caller* (module and function),
  not internal logging helpers.
- This is enforced by using an appropriate `stacklevel` in the `log.trace()` wrapper.

### Testing strategy

- Logging tests must not override logger levels with `NOTSET` when asserting semantic behavior.
- Tests attach `caplog.handler` explicitly to the non-propagating `fontshow` logger.
- A single parametrized test verifies:
  - `DEBUG` level → DEBUG only
  - `TRACE` level → DEBUG + TRACE
- Tests import the canonical `TRACE_LEVEL_NUM` from `fontshow.logging_utils`
  to avoid duplication and ensure consistency.

### D34 - Rationale

This approach:

- Preserves standard Python logging behavior
- Keeps TRACE noise fully opt-in
- Allows reliable debugging on systems with thousands of fonts
- Produces stable, future-proof logging tests

### D34 - Status

Accepted and implemented.

## D33 - Logging: reliable TRACE level and caller attribution

**Status**: PLANNED
**Tracked by**: #26, #29

### D33 - Context

Fontshow relies on a custom logging facade to provide optional, zero-overhead
diagnostics controlled via the `FONTSHOW_LOG_LEVEL` environment variable.
During Gentoo testing, TRACE logs were intermittently missing or reported
incorrect caller information.

### Problem

Two distinct issues were identified:

1. Logging wrappers (`log.trace`, `log.debug`, etc.) masked the real caller,
   causing all records to appear as originating from `logging_utils`.
2. TRACE records were silently filtered due to:
   - handler and logger level misalignment
   - propagation to the root logger
   - multiple imports and CLI entrypoint reconfiguration

Additionally, incorrect use of `stacklevel` caused runtime errors when applied
both in the facade and in the logger monkey-patch.

### D33 - Decision

The logging system is structured as follows:

- Caller attribution (`module` / `funcName`) is handled **exclusively** by the
  logging facade using `stacklevel`.
- The custom `Logger.trace` monkey-patch must **not** inject `stacklevel`.
- The `fontshow` logger explicitly disables propagation
  (`logger.propagate = False`) to prevent external logging configuration
  (e.g. pytest, `basicConfig`) from altering effective log levels.
- When `FONTSHOW_LOG_LEVEL` is set, both logger and handler levels are
  force-aligned to the requested level on every configuration pass.

### D33 - Consequences

- TRACE logging is deterministic across CLI entrypoints, pytest, and `python -m`
  execution.
- Caller context is preserved without performance-heavy stack inspection.
- Fontshow logging is isolated from the root logger and external frameworks.

This behavior is considered part of the public debugging contract of Fontshow.

## D32 - Decision: Changelog as a derived summary, not a source of truth

**Status**: PLANNED
**Tracked by**: #26, #29

### D32 - Decision

`CHANGELOG.md` is treated as a **derived, human-readable summary**.

It is **not** the authoritative record of changes.

Authoritative sources are:

- Git history and tags
- GitHub Releases (semantic-release)
- `decisions.md`

### D32 - Rationale

- Avoid duplication between automated and manual documentation
- Keep design intent and rationale in one place
- Allow the changelog to remain concise and readable

### D32 - Consequences

- The changelog summarizes *what* changed, not *why*
- Design rationale must always be captured in `decisions.md`

## D31 - CLI return code contract

**Status**: PLANNED
**Tracked by**: #26, #29

All Fontshow CLI commands adhere to the following return code contract:

- `0` — successful execution
- `1` — unrecoverable execution failure
- `2` — command-line usage error (handled by argparse)

Warnings do not affect the return code unless explicitly promoted
by the command logic.

This contract applies uniformly to all subcommands and entrypoints.

### D31 - Status

Documented and enforced through CLI tests.

## D30 - RuntimeWarning when executing `fontshow preflight`

**Status**: PLANNED
**Tracked by**: #26, #29

### D30 - Context

When executing:

```bash
fontshow preflight
```

Python may emit a RuntimeWarning indicating that
`fontshow.preflight.__main__` was already present in `sys.modules`
before execution.

This is caused by importing the preflight CLI entrypoint as part of the
dispatcher initialization, and then re-executing it via `-m`.

### D30 - Decision

The warning is acknowledged and accepted.

- Functional behavior is correct
- Output and exit codes are unaffected
- The supported and documented entrypoint is:
  `fontshow preflight`

Direct `python -m` execution remains best-effort and supported,
but is not the primary CLI path.

### D30 - Rationale

Eliminating the warning would require restructuring the preflight package
(e.g. separating CLI logic into a dedicated module), which is not justified
at this stage.

### D30 - Status

Known and accepted.

## D29 - Preflight command output and rendering responsibility

**Status**: Implemented
**Date**: 2026-01-08
**Scope**: `preflight`

### D29 - Context

The preflight subsystem already provided a structured rendering layer
(`render_preflight_results`) producing formatted output lines.
After CLI refactoring, the rendered output was no longer emitted,
causing silent execution despite successful checks.

### D29 - Decision

The responsibility for emitting preflight output belongs to the
preflight CLI boundary, not to the core execution logic.

Specifically:

- `run_preflight()`:
  - performs checks
  - returns structured results
  - produces no CLI output

- `render_preflight_results()`:
  - formats results into human-readable lines
  - does not print

- `preflight.main(args)`:
  - invokes rendering
  - prints rendered lines
  - prints a final summary line:
    - "Preflight passed."
    - "Preflight failed."
  - honors `--quiet` and `--verbose` flags
  - returns an exit code

The dispatcher invokes the preflight command through a local wrapper,
ensuring compatibility with existing CLI tests and monkeypatching.

### D29 - Rationale

This preserves:

- separation between logic and presentation
- backward-compatible CLI behavior
- existing test expectations

while keeping preflight consistent with the unified CLI contract.

### D29 - Status

Implemented and validated via CLI tests and manual execution.

## D28 - CLI execution model unification (dispatcher vs module entrypoints)

**Status**: Implemented
**Date**: 2026-01-08
**Scope**: `preflight` `dump_fonts.py` `parse_font_inventory.py` `create_catalog.py`

### D28 - Context

Fontshow commands can be executed through two different entrypoints:

- the unified dispatcher:
  `fontshow <command> [options]`
- direct module execution:
  `python -m fontshow.<module> [options]`

Historically, these entrypoints evolved independently, leading to:

- duplicated argument parsing
- inconsistent CLI options
- incompatible `main()` function signatures
- improper use of `sys.exit()` inside command logic

### D28 - Decision

All Fontshow CLI commands must follow a single, uniform execution contract:

- Each command exposes a callable:

  ```python
  def main(args) -> int
  ```

- `main(args)`:
  - contains *only* command logic
  - returns an integer exit code
  - MUST NOT call `sys.exit()`
  - MUST NOT perform argument parsing

- Argument parsing is performed exclusively:
  - in the dispatcher (`fontshow/__main__.py`)
  - or in the module `if __name__ == "__main__"` block for `python -m` usage

- `sys.exit()` is allowed **only** in:
  - the dispatcher entrypoint
  - module-level `__main__` blocks

### D28 - Rationale

This model:

- guarantees identical behavior across all entrypoints
- simplifies testing (no hidden exits)
- makes return codes explicit and testable
- prevents future CLI divergence

### D28 - Status

Applied to:

- `dump_fonts`
- `parse_font_inventory`
- `create_catalog`
- `preflight`

## D27 - C-Step: Charset-driven enrichment (5.1–5.3)

**Status**: Implemented
**Date**: 2026-01-07
**Scope**: `parse_font_inventory.py`
**Related components**: `dump_fonts.py`, `infer_languages.py`

---

### D27 - Context

Fontshow inventories may optionally include raw FontConfig charset data
at file level (produced by `dump_fonts.py` when enabled).
Prior to this step, charset data was collected but not consumed by the
parsing or inference pipeline.

At the same time, language and script inference relied exclusively on
Unicode block coverage derived from other sources, without leveraging
the potentially richer information provided by the charset.

---

#### D27 - Decision

We introduced a **three-phase, non-invasive enrichment pipeline**
based on FontConfig charset data:

##### 5.1 — Charset normalization

- Raw charset ranges are normalized into a deterministic, merged form.
- The result is attached as `coverage.normalized_charset`.
- No semantic interpretation is performed at this stage.

##### 5.2 — Unicode blocks derived from charset

- Normalized charset ranges are mapped to Unicode blocks using the
  existing `UNICODE_BLOCKS` table.
- The result is attached as `coverage.unicode_blocks_from_charset`.
- Existing `coverage.unicode_blocks` data is left untouched.

##### 5.3 — Script coverage derived from charset

- Charset-derived Unicode blocks are mapped to script coverage ratios
  using the existing `UNICODE_SCRIPT_RANGES` table.
- The result is attached as `coverage.script_coverage_from_charset`.
- This data is purely diagnostic and does not affect script inference.

Each phase:

- Is deterministic and idempotent
- Produces explicit, separate metadata
- Emits per-font DEBUG logs for observability
- Is covered by unit and integration tests

---

### D27 - Rationale

This approach deliberately avoids premature semantic decisions:

- Charset-derived data is **added**, never merged or substituted.
- No automatic fallback or precedence rules are introduced.
- Inference logic remains unchanged.

By keeping raw, normalized, and derived representations separate,
we preserve auditability and allow future policy decisions to be
made explicitly and incrementally.

---

### D27 - Consequences

- Inventories may now contain additional optional coverage fields:
  - `normalized_charset`
  - `unicode_blocks_from_charset`
  - `script_coverage_from_charset`
- These fields are not yet reflected in the JSON schema.
- Consumers must treat them as optional and informational.

A follow-up decision is required to determine whether:

- the existing schema version (1.1) should be extended, or
- a new schema version should be introduced to formalize these fields.

### Follow-ups

- Evaluate schema evolution strategy for charset-derived metadata.
- Decide if and how charset-driven signals should influence inference
  in future C-steps.

## D26 - Decision — Charset lifecycle and current non-consumption

**Status**: Implemented

### D26 - Context

FontConfig-derived charset metadata is currently extracted during the
`dump_fonts` stage and preserved in the raw inventory.

Specifically:

- `dump_fonts.py` invokes `fc-query` and extracts a raw FontConfig charset blob
  (when `--include-fc-charset` is enabled),
- the charset is serialized into the inventory under:

```text
  font["coverage"]["charset"]
```

- the raw inventory schema (`schema_version = 1.0`) explicitly allows the
  presence of this field.

### Current behavior

At the time of writing:

- `parse_font_inventory.py` **does not consume or interpret charset data**,
- charset metadata is treated as **informational-only**,
- no normalization, validation, or policy decision is applied to the charset,
- charset data does **not influence**:
  - Unicode block coverage,
  - script inference,
  - language inference,
  - semantic validation.

This behavior is **intentional** and reflects the current scope of the pipeline.

### D26 - Rationale

The decision to preserve but not consume charset metadata allows:

- forward compatibility with future enrichment steps,
- lossless propagation of FontConfig information,
- deferred design decisions around charset semantics.

Avoiding premature consumption prevents:

- accidental coupling between FontConfig output and inference logic,
- silent behavioral changes without explicit design review.

---

### Implications

- The presence of charset metadata in the inventory **does not imply usage**.
- The `--include-fc-charset` flag guarantees extraction and serialization,
  not semantic interpretation.

## D25 - Decision: Introduce a minimal structured logging infrastructure

### D25 - Status

- **Status:** Accepted, Implemented
- **Date:** 2026-01-06
- **Scope:** Structured logging infrastructure for Fontshow

Implementation planned as a dedicated, incremental step.

### D25 - Context

The project currently relies on ad-hoc debugging techniques
(`print(...)`, temporary variables, local debug code) to inspect internal
behavior during development and troubleshooting.

This approach has become fragile and inconsistent, especially while
debugging complex pipelines such as Fontconfig-based metadata extraction
(e.g. `--include-fc-charset` on Gentoo Linux).

### D25 - Decision

We introduce a minimal, disciplined, and opt-in structured logging
infrastructure to replace ad-hoc debugging across the project.

The logging system is designed as a lightweight wrapper around Python’s
standard `logging` module and provides a single, coherent mechanism for
observability.

The logging infrastructure must preserve caller module and function
information to allow precise attribution of log events without requiring
explicit identifiers in the payload.

### Design (initial scope)

- New internal logging utility module (e.g. `fontshow/logging_utils.py`)
- Supported log levels:
  - ERROR
  - WARNING
  - INFO
  - DEBUG
  - TRACE (custom, optional)
- Logging is disabled by default
- Activation via environment variable:

  `FONTSHOW_LOG_LEVEL=DEBUG`

- No external dependencies
- Zero functional overhead when disabled

### Usage model

The logging API is intentionally minimal, for example:

- `log.debug("message", extra={...})`
- or equivalent convenience helpers

The logging system is intended to be used incrementally, starting from
critical debugging paths.

### Relation to existing debug code

Temporary debug logic currently present in `parse_font_inventory` will be
used as a reference during the initial adoption of structured logging.

Once equivalent or superior observability is achieved through the logging
infrastructure, the existing ad-hoc debug code will be removed to avoid
duplication and maintenance overhead.

### D25 - Rationale

This approach enforces discipline, avoids over-design, and provides a
reusable foundation for future debugging and diagnostics, without
introducing permanent complexity or user-facing behavior changes.

### Logging messages — dump_fonts

| Module     | Function (scope) | Level   | Message                                     | When                                                 | Extra (keys)                               |
|------------|------------------|---------|---------------------------------------------|------------------------------------------------------|--------------------------------------------|
| dump_fonts | global           | INFO    | font inventory generation started           | At the beginning of inventory generation             | output_path, include_fc_charset, cache_dir |
| dump_fonts | global           | INFO    | font inventory generation completed         | At the end of inventory generation                   | total_fonts, include_fc_charset            |
| dump_fonts | global           | DEBUG   | fontconfig charset extraction enabled       | When --include-fc-charset flag is active             | query_mode                                 |
| dump_fonts | global           | DEBUG   | fontconfig charset extraction disabled      | When --include-fc-charset flag is not active         | —                                          |
| dump_fonts | global           | DEBUG   | font cache enabled                          | When --cache-dir flag is provided                    | cache_dir                                  |
| dump_fonts | global           | DEBUG   | font cache disabled                         | When --cache-dir flag is not provided                | —                                          |
| dump_fonts | global           | DEBUG   | font cache applied                          | When cache is effectively used (read/write/hit/miss) | cache_dir, operation                       |
| dump_fonts | per-file         | DEBUG   | fc-query invocation prepared                | Before invoking fc-query for a font                  | font_path, include_charset                 |
| dump_fonts | per-file         | TRACE   | fc-query executed                           | After fc-query execution                             | font_path, exit_code                       |
| dump_fonts | per-file         | TRACE   | fc-query raw output received                | When raw output is captured from fc-query            | font_path, stdout                          |
| dump_fonts | per-file         | DEBUG   | fontconfig output parsed                    | When fc-query output is successfully parsed          | font_path, fields_detected                 |
| dump_fonts | per-file         | DEBUG   | fontconfig output could not be parsed       | When fc-query output parsing fails                   | font_path, error_reason                    |
| dump_fonts | per-file         | DEBUG   | charset field detected in fontconfig output | When charset field is present in fc-query output     | font_path, ranges_count                    |
| dump_fonts | per-file         | DEBUG   | charset field missing in fontconfig output  | When charset field is absent in fc-query output      | font_path                                  |
| dump_fonts | per-file         | WARNING | fc-query execution failed                   | When fc-query exits with a non-zero status           | font_path, exit_code, stderr               |

---

### Note

The messages above operate at *font file level*, not at individual font
(face) level. At this stage of the pipeline, only the file path is known.
Per-font identifiers (font_id) are introduced later during inventory
enrichment and are therefore not available here.

### Logging messages — parse_font_inventory

| Module                | Function (scope) | Level   | Message                                   | When                                                   | Extra (keys)                                     |
|-----------------------|------------------|---------|-------------------------------------------|--------------------------------------------------------|--------------------------------------------------|
| parse_font_inventory  | global           | INFO    | font inventory parsing started            | At the beginning of inventory parsing                  | input_path, schema_version                       |
| parse_font_inventory  | global           | INFO    | font inventory parsing completed          | At the end of inventory parsing                        | total_entries, accepted_entries, ignored_entries |
| parse_font_inventory  | global           | DEBUG   | inference level enabled                   | When --infer-level flag is active                      | infer_level                                      |
| parse_font_inventory  | global           | DEBUG   | inference level applied                   | When inference logic is effectively applied            | infer_level, affected_features                   |
| parse_font_inventory  | global           | DEBUG   | inference disabled                        | When inference is not active                           | —                                                |
| parse_font_inventory  | global           | INFO    | inventory validation requested            | When --validate-inventory flag is active               | schema_version                                   |
| parse_font_inventory  | global           | DEBUG   | inventory validation started              | When validation phase begins                           | schema_version                                   |
| parse_font_inventory  | global           | INFO    | inventory validation passed               | When inventory validation succeeds                     | schema_version, validated_entries                |
| parse_font_inventory  | global           | ERROR   | inventory validation failed               | When inventory validation fails                        | schema_version, error_summary                    |
| parse_font_inventory  | per-font         | DEBUG   | font entry parsing started                | At the beginning of parsing a font entry               | font_id, font_path                               |
| parse_font_inventory  | per-font         | DEBUG   | font entry parsing completed              | After parsing a font entry                             | font_id, font_path, outcome                      |
| parse_font_inventory  | per-font         | DEBUG   | charset field missing in inventory entry  | When charset field is absent in inventory entry        | font_id, font_path                               |
| parse_font_inventory  | per-font         | DEBUG   | charset field empty in inventory entry    | When charset field is present but empty                | font_id, font_path, raw_charset                  |
| parse_font_inventory  | per-font         | DEBUG   | charset field available for normalization | When charset field is present and non-empty            | font_id, font_path, raw_charset_summary          |
| parse_font_inventory  | per-font         | DEBUG   | charset normalized                        | When charset normalization succeeds                    | font_id, font_path, normalized_summary           |
| parse_font_inventory  | per-font         | WARNING | charset normalization failed              | When charset normalization fails                       | font_id, font_path, failure_reason               |
| parse_font_inventory  | per-font         | DEBUG   | charset ignored by policy                 | When charset is ignored due to policy or configuration | font_id, font_path, policy_reason                |
| parse_font_inventory  | per-font         | DEBUG   | charset accepted                          | When charset is accepted and retained                  | font_id, font_path                               |
| parse_font_inventory  | per-font         | ERROR   | invalid font inventory entry              | When a font entry is structurally invalid              | font_id, font_path, validation_error             |

---

### Logging messages — infer_languages

| Module            | Function (scope) | Level   | Message                                  | When                                               | Extra (keys)                                       |
|-------------------|------------------|---------|------------------------------------------|----------------------------------------------------|----------------------------------------------------|
| infer_languages   | per-font         | DEBUG   | language inference started               | When language inference begins for a font entry    | font_id, font_path, infer_level                    |
| infer_languages   | per-font         | DEBUG   | language inferred from unicode coverage  | When a language is inferred using unicode coverage | font_id, font_path, inferred_languages, confidence |
| infer_languages   | per-font         | DEBUG   | language inference skipped               | When inference is skipped due to insufficient data | font_id, font_path, skip_reason                    |
| infer_languages   | per-font         | WARNING | language inference failed                | When inference logic fails unexpectedly            | font_id, font_path, failure_reason                 |

---

### Logging messages — schema_validation

| Module              | Function (scope) | Level   | Message                        | When                                                    | Extra (keys)                                |
|---------------------|------------------|---------|--------------------------------|---------------------------------------------------------|---------------------------------------------|
| schema_validation   | per-font         | DEBUG   | schema validation rule applied | When a schema validation rule is evaluated              | font_id, font_path, rule_id                 |
| schema_validation   | per-font         | WARNING | schema validation rule failed  | When a schema rule is violated but processing continues | font_id, font_path, rule_id, failure_reason |
| schema_validation   | per-font         | ERROR   | schema validation failed       | When schema validation fails fatally for an entry       | font_id, font_path, rule_id, error_summary  |

---

### Logging messages — semantic_validation

| Module                 | Function (scope) | Level   | Message                       | When                                                 | Extra (keys)                                        |
|------------------------|------------------|---------|-------------------------------|------------------------------------------------------|-----------------------------------------------------|
| semantic_validation    | per-font         | DEBUG   | semantic validation started   | When semantic validation begins for a font entry     | font_id, font_path                                  |
| semantic_validation    | per-font         | DEBUG   | semantic constraint satisfied | When a semantic constraint is satisfied              | font_id, font_path, constraint_id                   |
| semantic_validation    | per-font         | WARNING | semantic constraint violated  | When a semantic constraint is violated but tolerated | font_id, font_path, constraint_id, violation_reason |
| semantic_validation    | per-font         | ERROR   | semantic validation failed    | When semantic validation fails fatally for an entry  | font_id, font_path, constraint_id, error_summary    |

---

## D24 - Coverage Strategy and Rationale

- **Status:** Accepted, Implemented
- **Date:** 2026-01-05
- **Scope:** Test coverage policy for Fontshow

### D24 - Context

Fontshow includes a mix of:

- **Core logic modules** (validation, inference, preflight checks)
- **I/O-heavy pipeline components** (font discovery, catalog generation, LaTeX integration)
- **CLI entry points** and orchestration code

A full test suite is in place and currently executed on Linux (Gentoo) using `pytest` and `pytest-cov`.

At the time of this decision, the global coverage percentage reported by the tooling is relatively low (≈36%), despite all tests passing.

### Observations

Analysis of the coverage report shows that the low global percentage is primarily caused by two large modules:

- `fontshow/create_catalog.py`
- `fontshow/dump_fonts.py`

These modules:

- are heavily dependent on the host system (installed fonts, fontconfig, filesystem layout)
- interact with external tools (LuaLaTeX)
- perform long-running, side-effect-heavy operations
- are designed as **integration pipelines**, not as pure logic units

By contrast, the following areas show high coverage (typically 90–100%):

- Language and script inference
- Schema and semantic validation
- Inventory parsing and validation
- Preflight architecture (checks, registry, runner, rendering)
- Contract tests and policy enforcement

### D24 - Decision

The project **intentionally prioritizes meaningful, high-signal coverage** over a high global percentage.

Specifically:

- High coverage is required and enforced for:
  - core inference logic
  - validation and policy code
  - preflight checks and their contracts
- Low or zero coverage is currently accepted for:
  - CLI entry points
  - I/O-heavy pipeline modules
  - system-dependent integration code

The reported global coverage value is therefore considered **informational**, not a quality gate.

### D24 - Rationale

Attempting to raise global coverage by aggressively testing pipeline code would require:

- extensive mocking of system resources
- brittle test setups tied to specific Linux distributions
- tests that increase maintenance cost without improving confidence

Instead, the chosen approach:

- maximizes confidence in correctness where it matters
- keeps the test suite fast and deterministic
- aligns with the project’s long-term maintainability goals

### D24 - Consequences

- A low global coverage percentage is accepted and documented.
- Contributors are encouraged to add tests to core logic modules, not to inflate coverage numbers.
- Coverage reports must be interpreted per-module, not as a single aggregate metric.

### D24 - Future Work

Planned follow-up actions include:

- Introducing a `.coveragerc` file to:
  - exclude CLI entry points and selected pipeline modules
  - clarify the intended coverage scope
- Adding targeted tests for additional edge cases on native Linux (Gentoo)
- Potentially introducing integration-test markers for system-dependent paths

These improvements are explicitly deferred to a later phase.

**Decision summary:**
Coverage is treated as a qualitative signal, not a numerical target. The current strategy is intentional, documented, and aligned with the architecture of Fontshow.

## D23 - Decision: Script-aware sample text selection

- **Status:** Accepted, Implemented
- **Context:** Font catalog generation (`create_catalog`)
- **Related versions:** v0.20.0+

### D23 - Context

Fontshow supports rendering sample text for each font in the generated
catalog. Sample text can originate from two different sources:

1. **Embedded sample text**, extracted directly from the font file
   during `dump_fonts`.
2. **Inferred sample text**, selected at catalog generation time based
   on language inference results derived from Unicode coverage.

Previously, embedded sample text was always preferred whenever present,
regardless of its language or script compatibility with the dominant
font script. This behavior caused incoherent rendering for non-Latin
fonts (e.g. CJK fonts rendered with German or other Latin pangrams),
leading to cascading LuaLaTeX warnings and unreadable output.

### D23 - Decision

Embedded sample text is now used **only if its language matches the
primary inferred language** of the font.

If the embedded sample text language is incompatible with the dominant
inferred language, it is ignored and Fontshow falls back to selecting a
sample text based on language inference results.

Formally:

- Let `L₀` be the primary inferred language
  (`font["inference"]["languages"][0]`).
- Embedded sample text is used **only if**
  `sample_text.lang == L₀`.
- Otherwise, sample text is selected using inferred language-based
  fallback logic.

### D23 - Rationale

- Fontshow is an **analysis and cataloging tool**, not a raw font viewer.
- Script and language coherence is more important than strict fidelity
  to embedded font metadata.
- Embedded sample text is often Latin-based even in fonts whose dominant
  coverage is non-Latin.
- Using script-incompatible sample text leads to misleading output and
  LaTeX compilation issues.

This decision keeps inference policy centralized in
`parse_font_inventory` and ensures that `create_catalog` remains a pure
consumer of inference results.

### D23 - Consequences

- Catalog rendering is now consistent across scripts.
- Non-Latin fonts reliably render appropriate sample text.
- Embedded sample text is still preserved and used when compatible.
- No behavior change for purely Latin fonts.

### Alternatives considered

- Always prefer embedded sample text (rejected: causes incoherent output).
- Add user-facing flags to choose precedence (postponed; increases
  complexity without clear immediate benefit).

## D22 - Decision: Preflight checks refactoring to a class-based, registry-backed model

- **Status**: Accepted, Implemented
- **Date**: 2026-01-04
- **Scope**: `fontshow.preflight`

### D22 - Context

The original preflight subsystem started as a function-based implementation,
where each check was exposed as a standalone function and orchestrated by the
runner through a static dispatch table.

As the number of checks and policies grew, several issues emerged:

- Tests required extensive monkeypatching of internal functions.
- There was no explicit contract defining what a “check” was.
- Adding or composing checks for testing purposes was fragile.
- Static analysis tools (ruff, pylance) conflicted with dynamic dispatch.
- The runner API became increasingly difficult to reason about.

At the same time, we needed to preserve:

- Deterministic execution order
- `enabled` / `disabled` filtering semantics
- Test isolation and safety
- Backward-compatible CLI behavior

### D22 - Decision

We refactored the preflight subsystem to a **class-based model**, centered around
an explicit abstract base class and a lightweight registration mechanism.

The main elements of the new design are:

#### 1. `BaseCheck` abstract contract

All preflight checks now subclass a common abstract base class:

- Enforces the presence of:
  - a `check_id` class attribute
  - a `run()` method returning a `CheckResult`
- Provides a clear, inspectable contract for both production code and tests
- Enables static tooling to reason about the system

This makes the notion of “a check” explicit and verifiable.

#### 2. Explicit registry for checks

Checks are registered automatically when their class is defined.

The registry:

- Tracks all known check classes
- Allows test-only or experimental checks to exist without polluting the runner
- Supports controlled extensibility without dynamic imports

Importantly, **built-in checks remain explicitly listed** in the runner via
`CHECKS`, preserving clarity and determinism.

#### 3. Runner as a stable, testable orchestration layer

The runner now:

- Exposes its dependent modules (`environment`, `font_discovery`, `latex`)
  explicitly to support safe and explicit monkeypatching in tests
- Resolves checks using a clear priority order:
  1. Explicit `checks` argument (advanced usage, tests)
  2. Registered checks
  3. Built-in `CHECKS` fallback
- Preserves `enabled` / `disabled` filtering semantics

This results in a runner that is:

- Predictable
- Test-friendly
- Statistically analyzable
- Backward-compatible

### D22 - Consequences

#### Positive

- Stronger contracts and clearer architecture
- Tests assert behavior, not implementation details
- Reduced friction between runtime flexibility and static analysis
- Preflight subsystem is now considered **stable**, not experimental

#### Trade-offs

- Slightly higher upfront complexity compared to a function-based approach
- Requires discipline to keep test-only checks isolated

### Notes

- Sentinel or test-only checks may exist in the registry but are never executed
  by the runner unless explicitly requested.
- Contract tests ensure all production checks comply with `BaseCheck`.
- This design intentionally avoids implicit auto-discovery via imports.

### References

- `fontshow/preflight/checks/base.py`
- `fontshow/preflight/runner.py`
- `tests/preflight/test_base_check_contract.py`

## D21 - Decision: Move preflight subsystem to a class-based design

**Status**: Implemented

### D21 - Context

The initial implementation of the preflight subsystem was function-based.
While simple, this approach quickly showed limitations when introducing:

- Fine-grained policy tests (environment matrix, capability checks)
- Selective execution (enabled / disabled checks)
- Deterministic ordering and extensibility
- Robust monkeypatching in tests without relying on import hacks

Several iterations revealed that a purely function-based model made the
runner harder to test and reason about as the system grew.

### D21 - Decision

We refactored the preflight subsystem to a **class-based design**, centered on
an explicit `BaseCheck` abstract contract.

Each preflight check is now represented by a class that:

- Exposes a stable `check_id`
- Implements a `run() -> CheckResult` method
- Encapsulates its own execution logic

The runner (`run_preflight`) executes checks by instantiating these classes
from a deterministic registry (`CHECKS`).

### Why a BaseCheck abstract class

Introducing `BaseCheck` provides:

- A clear and enforceable contract for all checks
- Static guarantees (via typing) about the check interface
- A foundation for future validation and tooling

A dedicated test ensures that all registered checks comply with this contract,
preventing silent divergence over time.

### Why the runner exposes modules explicitly

The runner intentionally exposes the following modules as part of its public API:

- `environment`
- `font_discovery`
- `latex`

This design allows tests to safely monkeypatch environment detection and
capability probes without relying on fragile import-path tricks.

This is a deliberate trade-off favoring **testability and transparency**
over strict encapsulation.

### Check selection semantics

The runner supports selective execution through:

- `enabled`: run only checks whose `check_id` is included
- `disabled`: skip checks whose `check_id` is included

If both are provided, `enabled` is applied first, then `disabled`.

The `CHECKS` registry remains the authoritative list of built-in checks and is
not dynamically extended at runtime.

### D21 - Status

With this refactor and the accompanying test coverage, the preflight subsystem
is now considered **stable** rather than experimental.

## D20 - Decision: Transition to a Class-Based Model for Preflight Checks

- **Status:** Accepted, Implemented
- **Area:** Preflight / Testing / Architecture
- **Date:** 2026-01-03

### D20 - Context

The preflight checking system was initially implemented using a
**function-based model**, where the runner directly invoked functions
such as `check_environment()`, `check_font_discovery()`, etc.

As the project evolved and a more comprehensive test suite was introduced
— especially *policy-oriented tests* — several structural limitations
became evident:

- difficulty performing **selective monkeypatching** of dependencies
- implicit coupling between the runner and check implementations
- lack of a shared abstraction representing the concept of a “check”
- weaker domain semantics: a function does not model a first-class entity

In particular, the test suite required:

- explicit access to `check_id`
- fine-grained inspection of `CheckResult` objects
- controlled simulation of OS, execution mode, and tool availability
- long-term stability of the API used by tests

### D20 - Decision

The preflight subsystem was refactored to adopt a **class-based model**,
where each check is represented by a class exposing a `run()` method
that returns a `CheckResult`.

The runner maintains an **explicit registry of check classes** and is
responsible solely for orchestration.

Conceptual example:

```python
class FontDiscoveryCheck:
    check_id = "font_discovery.capability"

    def run(self) -> CheckResult:
        ...
```

### D20 - Rationale

The class-based model provides:

- an explicit representation of the *check* domain concept
- clearer execution flow
- more readable, stable, and less fragile tests
- a clean separation between:
  - check logic
  - orchestration (runner)
  - output rendering (CLI)

This approach also enables the future introduction of an
**abstract base class (`BaseCheck`)** to serve as a formal contract
for all preflight checks.

### D20 - Consequences

- Slightly increased verbosity in the implementation
- Significantly improved robustness, extensibility, and maintainability
- Easier and safer addition of new checks

## D19 - Decision: Explicit Exposure of Check Modules in the Runner

- **Status:** Accepted, PLANNED
- **Tracked by**: #26
- **Notes**: Logging spec ahead of implementation
- **Area:** Testing / Public API
- **Date:** 2026-01-03

### D19 - Context

The test suite relies on `pytest.monkeypatch` to simulate different
environmental conditions (OS, execution mode, tool availability).

To do so, tests intentionally reference symbols such as:

```python
runner.environment.detect_os
runner.font_discovery.has_fontconfig
runner.latex.has_lualatex
```

Linting tools such as **ruff** tend to flag these imports as unused or
attempt to remove them, as their usage is indirect.

### D19 - Decision

The `fontshow.preflight.runner` module explicitly exposes the following
modules as part of its **intentional public API**:

- `environment`
- `font_discovery`
- `latex`

This is a deliberate design choice and is documented as such.

### D19 - Rationale

- the test suite intentionally depends on these symbols
- the runner acts as a stable *facade* for the preflight subsystem
- this avoids fragile solutions (`# noqa`, dynamic imports, test-only hacks)

### D19 - Consequences

- the runner exposes a slightly broader public surface
- the relationship between tests and code becomes explicit and understandable
- instability between linting and runtime behavior is eliminated

## D18 - Decision: Font discovery preflight checks rely on fc-list only

- **Status:** Accepted, PLANNED
- **Tracked by**: #26
- **Notes**: Logging spec ahead of implementation
- **Context**: Preflight stage (C5.3)
- **Date**: 2026-01-03

### D18 - Decision

The preflight stage checks for font discovery capability by verifying the
presence of `fc-list` (fontconfig).

The presence of `fc-query` is intentionally **not** verified at preflight time.

### D18 - Rationale

- In standard Linux distributions, `fc-list` and `fc-query` are installed
  together as part of fontconfig.
- The preflight stage is intended to perform *capability checks*, not full
  runtime validation.
- Full font inspection (which requires `fc-query`) is performed during the
  pipeline execution and validated at runtime.
- Checking `fc-query` at preflight time could lead to premature failures in
  minimal or CI environments without providing actionable benefit.

### D18 - Consequences

- Preflight may succeed even if `fc-query` is missing.
- Missing `fc-query` will be detected later by the pipeline stages that require it.
- This decision simplifies the preflight logic and keeps it aligned with its
  intended scope.

### Future considerations

A pluggable font discovery backend architecture is planned for v2.x.y.
At that stage, backend-specific requirements (including `fc-query`) will be
validated as part of backend selection and runtime readiness checks.

## D17 - Decision: Font Discovery

- **Status:** Accepted, PLANNED
- **Tracked by**: #26
- **Notes**: Logging spec ahead of implementation

### D17 - Context

Font discovery is currently capability-based.

### D17 - Decision

A pluggable backend architecture is intentionally deferred to v2.x.y.

## D16 - Decision: Commit Signing Enforcement and CI Automation

### D16 - Context

The project requires strong guarantees about the integrity and provenance
of commits on the `main` branch.

The initial goal was to achieve **all of the following simultaneously**:

1. All commits cryptographically signed and verified by GitHub
2. Fully automated releases using `semantic-release` running in GitHub Actions
3. GitHub acting as the sole enforcer and source of truth

### Attempted Approaches

Several configurations were evaluated:

#### A. Branch Protection Rules with “Require signed commits”

- Result: ❌ CI commits rejected
- Reason: GitHub Actions cannot produce commits with *verified* signatures

#### B. Repository Rulesets with signed-commit enforcement

- Result: ❌ Same limitation as above
- Rulesets enforce signing correctly but do not distinguish CI-generated commits

#### C. GPG / SSH signing inside GitHub Actions

- Result: ❌ Not viable
- GitHub does not associate CI-generated signatures with a verified identity

#### D. Forcing semantic-release to avoid commits

- Result: ⚠️ Partial
- Would require abandoning `@semantic-release/git`
- Incompatible with current release workflow

### D16 - Decision

Fontshow adopts the following model:

- GitHub **Repository Rulesets** enforce commit signing
- **Human-authored commits must be signed**
- **CI automation is explicitly trusted and documented**
- GitHub remains the authoritative enforcement layer

This is the **only configuration that is both technically feasible
and auditable** with current GitHub capabilities.

### D16 - Consequences

- Local hooks are advisory, not authoritative
- CI automation is trusted by policy, not by cryptographic proof
- The decision may be revisited if GitHub introduces verified CI signatures

## D15 - Decision: Version bumps driven by Conventional Commits

- **Status:** Accepted, PLANNED
- **Tracked by**: #26
- **Notes**: Logging spec ahead of implementation

### D15 - Decision

Fontshow version increments are driven exclusively by **Conventional Commits**
in combination with `semantic-release`.

- `fix:` → patch release
- `feat:` → minor release
- `BREAKING CHANGE:` → major release

The effective version is materialized via Git tags and resolved at runtime.

### D15 - Rationale

- Version numbers reflect semantic changes
- No manual version editing in source files
- Git history becomes part of the public API contract

### D15 - Consequences

- Incorrect commit types produce incorrect versions
- Developers must treat commit messages as authoritative

## D14 - Decision: Single-source-of-truth versioning

**Status:** IMPLEMENTED, OBSOLETE

### D14 - Decision

Fontshow uses a **single-source-of-truth versioning model**:

- Version defined in `pyproject.toml`
- Retrieved at runtime via:

```python
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("fontshow")
except PackageNotFoundError:
    __version__ = "0.0.0"
```

- All CLI tools import the version from `fontshow.__version__`

### D14 - Consequences

- Git tags, package metadata, CLI output and generated artifacts are consistent
- No duplicated version constants

## D13 - Decision: Deferred Warning Emission via Structured Collection

**Status:** IMPLEMENTED, OBSOLETE

### D13 - Decision

Validation warnings are **not emitted directly**.
They are collected as structured records and returned to the caller.

### D13 - Rationale

- Deterministic testing
- Configurable verbosity
- Machine-readable export

### D13 - Consequences

- CLI flags (`--verbose`, `--quiet`) control presentation only
- Core logic remains side-effect free
- Warning handling via structured accumulator
- No printing in leaf validators

## D12 - Decision: Coverage reporting without enforcement

**Status:** IMPLEMENTED, OBSOLETE

### D12 - Decision

Test coverage is measured and reported, but **no minimum threshold is enforced**.

### D12 - Rationale

- Some code interacts with external systems
- Coverage is informative, not a gate

**Status**
Accepted

## D11 - Decision: CI quality gates via pre-commit and pytest

**Status:** IMPLEMENTED, OBSOLETE

### D11 - Decision

The **test job** in CI enforces quality via:

- `pre-commit run --all-files`
- `pytest`

The **docs job** only builds documentation.

### D11 - Rationale

- Clear separation of concerns
- CI mirrors local developer workflow

### D11 - Consequences

- The CI pipeline fails early if code quality checks do not pass
- Tooling such as `ruff` is managed exclusively via `.pre-commit-config.yaml`
- Additional quality gates (coverage, type checking) can be added to the test job
  without affecting documentation deployment
- Developers can rely on CI to mirror local pre-commit behavior

## D10 - Decision: Separate CI jobs for tests and documentation

**Status:** IMPLEMENTED, OBSOLETE

### D10 - Decision

Tests and documentation are executed in **separate CI jobs**.

### D10 - Rationale

- Failures are easier to diagnose
- Documentation issues do not block test feedback

## D9 - Decision: Font entry `family` field required at top-level

**Status:** IMPLEMENTED, OBSOLETE

### D9 - Decision

Each font entry **must** include a top-level `family` field.

### D9 - Rationale

- Unambiguous grouping
- Simple and deterministic validation

## D8 - Decision C4.2.2 — Script inference based on Unicode coverage

### D8 - Decision

Script inference is performed using Unicode coverage metadata
and normalized to **ISO 15924** codes.

Fallback logic is used when block-level data is unavailable.
The inference strategy follows a two-step approach:

1. **Primary source**: Unicode block statistics (`coverage.unicode_blocks`)
2. **Fallback**: Maximum Unicode code point (`coverage.unicode.max`)

All outputs are normalized to ISO 15924 codes and stored in
`fonts[].inference.scripts`.

If no reliable inference is possible, the value `["unknown"]` is emitted.

### D8 - Context

Fontshow needs a consistent and portable way to infer the writing systems
supported by a font, independently of platform-specific metadata and
language declarations.

Available inputs include:

- Unicode block usage statistics (FontConfig / fc-query)
- Unicode code point coverage (fontTools)

### D8 - Rationale

- Unicode coverage is more stable and portable than language tags.
- ISO 15924 provides a compact, standardized representation of writing systems.
- Separating scripts from languages avoids false assumptions and simplifies
  downstream processing.
- The fallback mechanism ensures robustness when block-level data is unavailable.

### D8 - Consequences

- `fonts[].inference.scripts` is best-effort and non-authoritative.
- Downstream tools must tolerate `"unknown"` and missing values.
- Language inference is handled separately and may not align one-to-one with
  script inference.

## D7 - Exclude coverage artifacts from version control

### D7 - Decision

Coverage artifacts generated by `pytest-cov` (e.g. `.coverage`,
`coverage.xml`, `htmlcov/`) are excluded from version control and treated
as disposable local artifacts.

### D7 - Rationale

These files are environment-specific, non-deterministic, and can be
regenerated at any time. Storing them in the repository would add noise
without long-term value.

## D6 - Work tracking and technical debt

- **Status**: ONGOING
- **Note**: Logging specifications intentionally precede implementation.
- TODOs, bugs, and technical debt are tracked **exclusively via GitHub Issues**.
- Static TODO files in the repository are not used.
- Issues represent the operational state of the work.

## D5 - Development environment

- Development takes place in Linux and Linux-like environments (including WSL).
- Differences between environments are considered part of the problem domain.
- Validation on native Linux is considered necessary for critical functionality.

## D4 - Testing and quality

- Automated tests are based on **pytest**.
- Quality checks include linting and static validation tools.
- CI is considered the final authority on code quality.

## D3 - Documentation

- Official project documentation is maintained using **MkDocs**.
- The README and cheat-sheets are derived from the MkDocs documentation.

## D2 - Data handling

- Raw data is not modified or “cleaned” silently.
- Normalization:
  - does **not replace** original values;
  - adds normalized versions alongside the original data.
- The  **Schema** and the **Data Dictionary** are the normative reference for the meaning of data fields.

## D1 - Language and project structure

- **Python** is the primary language of the project.
- The project is structured as a **package**, not as a collection of standalone scripts.
- Module execution is preferably performed using:
  - `python -m <module>`
