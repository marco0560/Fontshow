# Decision 0024 - Parse-inventory validation summary and fallback handling

**Date**: 14/03/2026
**Status**: Accepted

## Context

The `parse-inventory` stage enriches raw `dump-fonts` output.

This enrichment is explicitly responsible for:

- inferring languages when no declared language metadata is available
- generating a specimen from curated script samples or cmap fallback when
  the font does not provide a usable internal sample

Prior to this decision, `fontshow parse-inventory -I` used entry-level
validation rules and per-font warning emission that treated these
expected fallback outcomes as if they were user-actionable problems.

In practice this produced two issues:

1. **False fatal validation failures**

   Enriched inventories with:

   - empty `sample_text.text`
   - valid `specimen_text`
   - valid `specimen_strategy`
   - valid `specimen_glyph_count`

   were reported as invalid, even though the pipeline had already
   generated a usable specimen as designed.

2. **Excessive warning noise**

   `parse-inventory -I` emitted one warning line per font for conditions
   such as:

   - `missing_declared_languages`
   - `specimen_cmap_fallback`

   On large inventories this produced thousands of lines of output while
   conveying very little actionable information.

This behavior conflicted with the intent of the parse stage and with the
project’s CLI verbosity principles:

- expected fallback behavior should not be reported as validation failure
- routine enrichment observations should be summarized, not spammed
- verbose mode may add detail, but default mode must remain readable

## Decision

`parse-inventory` validation and reporting are adjusted as follows.

### 1. Empty internal sample text is not fatal

During validation of enriched inventories, `sample_text.text` is allowed
to be an empty string as long as it remains structurally valid text.

The downstream usability contract is determined by the final specimen
fields:

- `specimen_text`
- `specimen_strategy`
- `specimen_glyph_count`

This reflects the fact that internal font sample text is optional input,
while the generated specimen is the actual output consumed downstream.

### 2. Expected enrichment fallbacks are not stored as per-font warnings

The enrichment stage no longer emits per-font warning records for:

- `missing_declared_languages`
- `specimen_cmap_fallback`

These conditions are considered normal enrichment observations, not
anomalies.

### 3. Validation output is grouped by category

`fontshow parse-inventory -I` no longer prints one line per font for
embedded warning records.

Instead, validation emits:

- a grouped warning summary for actionable warning categories
- a grouped observation summary for expected fallback outcomes
- optional verbose example blocks for inspection

This preserves observability while keeping default output concise.

### 4. Success output remains single-pass

Validate-only mode no longer duplicates the success line already emitted
 by the validation layer.

## Consequences

Positive:

- `parse-inventory -I` now reflects the actual semantics of enrichment
- enriched inventories are not rejected merely because the font lacked
  internal sample text
- routine fallback behavior is visible through summaries instead of log
  flooding
- default CLI output for large inventories is readable again
- verbose mode still allows diagnostic inspection

Negative:

- users no longer get an automatic per-font warning stream for these
  fallback cases
- deep inspection of fallback-heavy inventories now relies on:
  - verbose summary examples
  - direct inspection of the enriched JSON artifact
  - ad hoc tooling such as `jq`

## Alternatives considered

### Keep per-font warnings but only in `--verbose`

Rejected.

Even in verbose mode, one-line-per-font reporting for expected fallback
behavior is too noisy on large inventories.

### Continue treating empty `sample_text.text` as fatal

Rejected.

This contradicts the design of the enrichment stage, whose purpose is to
produce a usable final specimen when no internal sample is present.

### Write a separate machine-readable report as the primary solution

Deferred.

This remains a valid future enhancement, but grouped CLI summaries were
the smallest coherent fix for the current problem.

## Related components

- `parse-inventory` command
- inventory entry validation
- specimen generation
- language inference
- CLI validation reporting
