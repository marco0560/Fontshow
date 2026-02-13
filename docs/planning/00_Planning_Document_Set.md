# Fontshow — Planning Document Set (Base-Zero)

This document lists the planning and governance documents
to support the new base-zero roadmap. Each document is described
by title, function, and a one-line content summary.

## Authority and scope

This document set is the **canonical, normative source of truth**
for Fontshow project planning.

It defines:

- scope
- sequencing
- milestones
- constraints
- governance rules

All other planning-related documents (including the project roadmap)
are **derived, descriptive, and non-normative**.

The project roadmap is maintained for communication and orientation purposes:

- [`docs/roadmap.md`](../roadmap.md)

In case of conflicts or ambiguity, the planning document set
**always takes precedence**.

## Document Set

### 1. [ROADMAP](01_TIMELINE.md)

**Function:** Canonical, user-facing roadmap for the project.
**Content:** High-level phases, objectives, non-goals, and decision checkpoints from v0.28.7.post14 onward.

---

### 2. [PHASES](02_PHASES.md)

**Function:** Define the planning phase taxonomy and what work is allowed in each phase.
**Content:** Phase definitions, objectives, non-goals, and scope boundaries (conceptual, non-temporal).

---

### 3. [MILESTONES_DEFINITION](03_MILESTONES_DEFINITION.md)

**Function:** Define the new milestone taxonomy and semantics.
**Content:** Rules for milestone naming, scope size, completion criteria, and allowed content.

---

### 4. [ISSUE_MODEL](04_ISSUE_MODEL.md)

**Function:** Define what a “good issue” means in Fontshow.
**Content:** Issue sizing rules, session-sized constraints, labels, and lifecycle states.

---

### 5. [ATOMIC_ACTION_LIST](05_ATOMIC_ACTION_LIST.md)

**Function:** Low-level execution backlog derived from planning.
**Content:** Numbered, atomic, implementation-level actions traceable to issues and milestones.

---

### 6. [ISSUE_BACKLOG_SYNTHESIS](06_ISSUE_BACKLOG_SYNTHESIS.md)

**Function:** Bridge between atomic actions and GitHub issues.
**Content:** Grouping of atomic actions into session-sized GitHub issues, with rationale.

---

### 7. [TESTING_STRATEGY](07_TESTING_STRATEGY.md)

**Function:** Authoritative statement of Fontshow’s testing philosophy.
**Content:** Unit vs integration split, environment-dependent checks, CI policy, and coverage expectations.

---

### 8. [STABILIZATION_SCOPE](08_STABILIZATION_SCOPE.md)

**Function:** Define the stabilization phase contract (Phase 1).
**Content:** What qualifies as stabilization work, explicit exclusions, and acceptance criteria.

---

### 9. [HARDENING_AND_LOADABILITY_BASELINE](09_HARDENING_AND_LOADABILITY_BASELINE.md)

**Function:** Define the current hardening phase and the pre-Qt stabilization baseline.
**Content:** Refactoring boundaries, robustness fixes (specimen/loading), LuaLaTeX loadability persistence with runtime fingerprint, deterministic diagnostics (discovery vs loadable), and the “Qt only after baseline” gate.

---

### 10. [PIPELINE_ROBUSTNESS](10_PIPELINE_ROBUSTNESS.md)

**Function:** Capture resilience expectations for LaTeX and catalog generation.
**Content:** Failure isolation rules, diagnostics requirements, and survivability principles.

---

### 11. [GOVERNANCE_NOTES](11_GOVERNANCE_NOTES.md)

**Function:** Lightweight governance and decision-record container.
**Content:** How decisions are made, recorded, revised, and deprecated over time.

---

### 12. [V2_DESIGN_SPIKE](12_V2_DESIGN_SPIKE.md)

**Function:** Isolated design exploration document for v2.x.y.
**Content:** Architectural sketches, feasibility analysis, risks, and explicit non-commitments.

## Notes

- Documents 1–4 form the **core planning spine**.
- Documents 5–6 are **execution-facing** and may evolve more rapidly.
- Documents 7–10 are **contract documents**: changes must be explicit and justified.
- Document 9 is a contract-style planning bridge between stabilization (8) and pipeline robustness (10), and must be kept consistent with the Timeline (1).
- Document 12 is **non-binding by design** and must not leak into implementation work without approval.
