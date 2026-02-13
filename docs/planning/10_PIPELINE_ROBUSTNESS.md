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

## Rendering Robustness and Loadability Guarantees

As part of the pipeline hardening effort, the rendering stage must be resilient to environment-dependent variability and font-specific limitations.

### Catalog Non-Abort Requirement

Catalog generation must not abort due to:

- subset-empty conditions caused by specimen text not matching available glyphs,
- fragile name-based font loading or shape resolution failures,
- environment-dependent font loadability differences.

The rendering pipeline must guarantee safe and deterministic behavior even when individual fonts cannot be rendered under the current runtime.

### Loadability Persistence

The system persists LuaLaTeX loadability decisions in the inventory together with runtime metadata. This persistence serves two purposes:

- avoid repeated expensive probing,
- ensure deterministic behavior when the runtime environment has not changed.

Loadability information is considered valid only when the runtime fingerprint matches the environment under which it was computed.

When a mismatch is detected, the system must fall back to runtime validation without causing pipeline failure.

### Runtime Fingerprint as Robustness Mechanism

The runtime fingerprint provides a stable indicator of the LuaLaTeX environment relevant to font loading. It allows the system to:

- detect when persisted loadability may no longer be valid,
- preserve determinism within a stable environment,
- avoid silent inconsistencies between inventory and rendering behavior.

### Deterministic Diagnostics

The pipeline must support reproducible diagnostics that distinguish between:

- fonts discovered by the system,
- fonts loadable by the rendering engine,
- and their deterministic difference.

These diagnostics improve observability and help identify environment-dependent rendering limitations without compromising pipeline stability.

### Role in Stabilization

These guarantees contribute to the stabilization baseline by ensuring that:

- rendering failures are contained and non-fatal,
- environment-dependent variability does not cause non-deterministic behavior,
- loadability persistence remains a reliable component of the pipeline.

---

## Status

This pipeline robustness contract is **active** and governs
all catalog and LaTeX-related processing
from v0.28.7.post14 onward.
