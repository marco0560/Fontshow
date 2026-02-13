# Fontshow — Base-Zero Project Timeline

**Current version:** v0.28.7.post14

This timeline replaces all previous milestone plans.
Dates and phases are defined from scratch (“base-zero planning”)
and reflect the actual maturity and constraints of the project.

All phases end with an explicit decision checkpoint before proceeding.

---

## Phase 0 — Re-baseline, tooling & environment setup

### Weeks 1–2: Jan 13 – Jan 26

### Objectives Phase 0

- Reconstruct the real project state from code, tests, and documentation.
- Establish a clean, reproducible development environment.
- Normalize tooling and workflows across Linux, WSL, and Windows.

### Scope Phase 0

- Freeze existing planning artifacts as historical references.
- Audit current codebase, test suite, CLI behavior, and documentation.
- Finalize local tooling setup:
  - Python environment
  - pre-commit and git hooks
  - Node / semantic-release preview tooling
- Validate cross-environment behavior.
- Define:
  - new milestone taxonomy,
  - issue sizing rules,
  - definition-of-done template for issues.

### Non-goals Phase 0

- No functional changes.
- No new features.
- No refactors beyond tooling hygiene.

### Checkpoint Phase 0

- Planning framework approved and ready for execution.

---

## Phase 1 — Stabilization sprint

### Weeks 3–4: Jan 27 – Feb 9

### Objectives Phase 1

- Reduce friction and instability in existing functionality.
- Make implicit contracts explicit.

### Scope Phase 1

- Close high-impact refinements.
- Formalize behaviors already relied upon by code and tests.
- Identify and isolate technical debt that blocks later phases.

### Non-goals Phase 1

- No new feature development.
- No architectural redesign.

### Checkpoint Phase 1

- Stabilization scope validated.
- Optional stabilization release candidate identified.

---

## Phase 2 — Testing strategy & coverage alignment

### Weeks 5–11: Feb 10 – Mar 15

### Objectives Phase 2

- Make the test suite deterministic and environment-agnostic.
- Align coverage metrics with actual guarantees.

### Scope Phase 2

- Clear separation of unit vs integration tests.
- Explicit handling of environment-dependent checks.
- CI-safe defaults and documented coverage expectations.

### Non-goals Phase 2

- No feature work.
- No expansion of test surface beyond alignment needs.

### Checkpoint Phase 2

- Testing policy approved and enforced.

---

## Phase 3 — LaTeX & create_catalog robustness

### Weeks 12-15: Mar 16 – Apr 12

### Objectives Phase 3

- Improve pipeline survivability and diagnostics.

### Scope Phase 3

- Isolate failures caused by individual fonts.
- Improve error reporting and recovery paths.
- Document reproducibility and troubleshooting practices.

### Phase 3 — Extended Hardening Scope (Post-C5)

The LaTeX and catalog robustness phase has been extended to include a deterministic hardening layer aimed at eliminating environment-dependent rendering failures and preparing a stable baseline before any discovery backend transition.

This extended scope includes:

- A deterministic specimen strategy that prevents subset-empty failures during catalog generation.
- A path-first font loading strategy to reduce `.fontspec` name-resolution fragility, with safe fallback where necessary.
- A LuaLaTeX loadability validation step and persistence of the result in the inventory, together with runtime metadata describing the environment under which loadability was verified.
- A runtime fingerprint mechanism allowing the system to detect when persisted loadability is no longer valid and fall back to runtime validation.
- Deterministic diagnostic extraction of:
  - all discovered fonts,
  - LuaLaTeX-loadable fonts,
  - and their reproducible difference.
- Establishment of a stabilization baseline in which catalog generation cannot abort due to subset-empty or loadability-related failures.

This baseline is a prerequisite for any future work on alternative discovery backends (e.g. Qt-based discovery).

### Non-goals Phase 3

- No major pipeline redesign.
- No feature additions unrelated to robustness.

### Checkpoint Phase 3

- Pipeline resilience deemed acceptable for further evolution.

---

## Phase 4 — CLI UX & exit code contracts

### Weeks 16-17: Apr 13 – Apr 26

### Objectives Phase 4

- Consolidate CLI semantics and guarantees.

### Scope Phase 4

- Standardize exit codes and error signaling.
- Clarify human vs machine-readable output.
- Add regression tests for CLI contracts.

### Non-goals Phase 4

- No new commands.
- No CLI feature expansion.

### Checkpoint Phase 4

- CLI behavior considered stable and documented.

---

## Phase 5 — Charset-aware enrichment (feature evolution)

### Weeks 18-19: Apr 27 - May 10

### Objectives Phase 5

- Introduce charset decoding and enrichment in a controlled manner.

### Scope Phase 5

- Incremental, observable feature steps.
- Explicit non-goals for each step.
- Strong test and diagnostic coverage.

### Non-goals Phase 5

- No implicit scope expansion.
- No coupling to future v2 architecture.

### Checkpoint Phase 5

- Charset feature set evaluated for completeness and risks.

---

## Phase 6 — Governance & contributor experience

### Weeks 20-21: May 11 - May 24

### Objectives Phase 6

- Improve maintainability and contributor onboarding.

### Scope Phase 6

- Documentation indexing and navigation.
- Public vs internal API clarification.
- Governance and decision-record practices.

### Non-goals Phase 6

- No functional changes.

### Checkpoint Phase 6

- Project considered “contributor-ready”.

---

## Phase 7 — v2.x.y design spike (non-binding)

### Weeks 22-23: May 25 – Jun 7

### Objectives Phase 7

- Explore future architecture without commitment.

### Scope Phase 7

- Pluggable backend concepts.
- Interface sketches and feasibility analysis.
- Risk and complexity assessment.

### Non-goals Phase 7

- No implementation.
- No implicit roadmap commitment.

### Checkpoint Phase 7

- Explicit go / no-go decision for v2 planning.

---

## Global rules

- Each phase includes a 10–20% internal buffer.
- No feature expansion before Phases 1–2 are completed.
- Every phase ends with an explicit review and re-approval step.
