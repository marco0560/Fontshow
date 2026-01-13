# PIPELINE_ROBUSTNESS.md

## Fontshow — Pipeline Robustness and Failure Isolation

**Current version:** v0.28.7.post14
**Applies to:** Catalog generation, LaTeX processing, and related pipelines

---

## Purpose

This document defines the **robustness expectations** for the Fontshow
processing pipeline.

It establishes:
- failure isolation principles,
- diagnostic requirements,
- survivability rules,
- and reproducibility guidance.

This document is **normative**.

---

## Guiding Principles

- **Fail locally, not globally**
  A failure affecting a single font or asset MUST NOT invalidate
  the entire pipeline when avoidable.

- **Diagnose before aborting**
  Failures MUST produce actionable diagnostics before termination.

- **Survivability over perfection**
  Partial results are preferable to total failure when correctness
  is not compromised.

---

## Failure Classification

### Recoverable Failures

Examples:
- A single font fails to process.
- A LaTeX run fails for a specific document.
- Metadata decoding fails for a specific entry.

Expected behavior:
- Record the failure.
- Continue processing remaining items.
- Surface a summary at the end.

---

### Non-Recoverable Failures

Examples:
- Corrupt global configuration.
- Missing mandatory dependencies.
- Invalid invocation parameters.

Expected behavior:
- Abort execution.
- Emit a clear error message.
- Exit with the appropriate non-zero exit code.

---

## Diagnostics Requirements

For each failure, the pipeline MUST provide:

- Identification of the affected item.
- The stage at which the failure occurred.
- A concise description of the failure.
- Pointers to logs or artifacts when applicable.

Stack traces SHOULD NOT be shown by default unless explicitly requested.

---

## Logging and Reporting

- Logs MUST distinguish between:
  - warnings,
  - recoverable errors,
  - fatal errors.
- Summaries MUST include:
  - number of processed items,
  - number of failures,
  - number of skipped items.

---

## Reproducibility

To support reproducibility:

- The pipeline SHOULD emit:
  - version information,
  - relevant configuration parameters,
  - environment hints when applicable.

- Documentation MUST describe:
  - how to reproduce common failures,
  - known environment sensitivities.

---

## Testing Implications

- Failure scenarios MUST be covered by tests where feasible.
- Tests MUST validate:
  - correct classification of failures,
  - correct continuation or termination behavior.

Environment-dependent failure tests MUST be isolated.

---

## Relationship to CLI Contract

- Pipeline failures MUST map to documented CLI exit codes.
- The CLI MUST surface pipeline summaries clearly.

---

## Status

This pipeline robustness contract is **active** and governs
all catalog and LaTeX-related processing
from v0.28.7.post14 onward.
