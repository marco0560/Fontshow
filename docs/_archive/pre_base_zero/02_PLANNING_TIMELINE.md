# Archived after base-zero planning (v0.28.7.post14)

# PLANNING_TIMELINE.md

## Fontshow — Internal Planning Timeline

**Current version:** v0.28.7.post14
**Planning model:** Base-zero (supersedes all previous timelines)

---

## Purpose

This document defines the **internal execution timeline** for Fontshow,
derived from the approved base-zero roadmap.

It is intended for:
- project planning,
- issue sequencing,
- milestone definition,
- execution tracking.

Unlike `ROADMAP.md`, this document is **not user-facing** and may evolve
as execution progresses, provided changes are explicit and reviewed.

---

## Timeline Overview

| Phase | Name                                   | Dates               | Focus                              |
|------:|----------------------------------------|---------------------|------------------------------------|
| 0     | Re-baseline & tooling                  | Jan 13 – Jan 26     | Planning, tooling, environment     |
| 1     | Stabilization sprint                   | Jan 27 – Feb 9      | Contract formalization             |
| 2     | Testing strategy & coverage            | Feb 10 – Feb 23     | Deterministic tests, CI alignment  |
| 3     | LaTeX & catalog robustness             | Feb 24 – Mar 16     | Pipeline survivability             |
| 4     | CLI UX & exit code contracts           | Mar 17 – Mar 30     | CLI guarantees                     |
| 5     | Charset-aware enrichment               | Mar 31 – Apr 27     | Controlled feature evolution       |
| 6     | Governance & contributor experience    | Apr 28 – May 11     | Maintainability, onboarding        |
| 7     | v2.x.y design spike (non-binding)      | May 12 – May 25     | Architecture exploration           |

---

## Phase Details

### Phase 0 — Re-baseline, tooling & environment setup
**Jan 13 – Jan 26**

**Primary goals**
- Establish a reliable planning baseline.
- Normalize development tooling and workflows.
- Validate cross-environment reproducibility.

**Key outputs**
- Approved planning framework.
- Verified local tooling (Python, git hooks, pre-commit, Node tooling).
- Defined milestone and issue models.

**Entry criteria**
- v0.28.7.post14 tagged and stable.

**Exit criteria**
- Planning documents approved.
- Tooling validated on at least one reference environment.

---

### Phase 1 — Stabilization sprint
**Jan 27 – Feb 9**

**Primary goals**
- Reduce friction in existing functionality.
- Make implicit assumptions explicit.

**Key outputs**
- Stabilization scope definition.
- Closed or reclassified high-impact refinements.

**Entry criteria**
- Phase 0 completed.
- Issue model available.

**Exit criteria**
- Stabilization work either completed or explicitly deferred.
- Optional release candidate identified.

---

### Phase 2 — Testing strategy & coverage alignment
**Feb 10 – Feb 23**

**Primary goals**
- Deterministic test behavior across environments.
- Clear definition of test categories and coverage guarantees.

**Key outputs**
- Testing strategy document.
- CI-safe defaults enforced.

**Entry criteria**
- Stabilization phase complete.

**Exit criteria**
- Tests categorized and aligned with policy.
- Coverage metrics documented and meaningful.

---

### Phase 3 — LaTeX & create_catalog robustness
**Feb 24 – Mar 16**

**Primary goals**
- Improve robustness of catalog generation.
- Isolate and survive individual font failures.

**Key outputs**
- Improved diagnostics.
- Documented troubleshooting and reproducibility guidance.

**Entry criteria**
- Deterministic test baseline in place.

**Exit criteria**
- Pipeline survivability acceptable for feature evolution.

---

### Phase 4 — CLI UX & exit code contracts
**Mar 17 – Mar 30**

**Primary goals**
- Stabilize CLI semantics and exit codes.
- Support both human and automation use cases.

**Key outputs**
- CLI contract document.
- Regression tests for CLI behavior.

**Entry criteria**
- Pipeline robustness stabilized.

**Exit criteria**
- CLI behavior considered stable.

---

### Phase 5 — Charset-aware enrichment
**Mar 31 – Apr 27**

**Primary goals**
- Introduce charset decoding and enrichment incrementally.

**Key outputs**
- Observable feature steps.
- Strong diagnostics and tests.

**Entry criteria**
- CLI and pipeline stability achieved.

**Exit criteria**
- Charset feature scope evaluated and validated.

---

### Phase 6 — Governance & contributor experience
**Apr 28 – May 11**

**Primary goals**
- Improve long-term maintainability.
- Lower contribution barriers.

**Key outputs**
- Governance notes.
- Contributor-facing documentation improvements.

**Entry criteria**
- Core functionality stabilized.

**Exit criteria**
- Project considered contributor-ready.

---

### Phase 7 — v2.x.y design spike (non-binding)
**May 12 – May 25**

**Primary goals**
- Explore future architecture options.

**Key outputs**
- Design sketches.
- Feasibility and risk assessment.

**Entry criteria**
- Stable v0.x baseline.

**Exit criteria**
- Explicit go / no-go decision for v2 planning.

---

## Planning Rules

- Each phase includes an internal **10–20% buffer**.
- Scope expansion requires explicit review.
- No phase may start without completing the previous phase’s checkpoint.
- This timeline may be revised, but historical versions must be preserved.

---

## Status

This planning timeline is **active** and reflects the approved
base-zero plan as of v0.28.7.post14.
