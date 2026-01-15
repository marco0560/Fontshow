# Fontshow — Planning Document Set (Base-Zero)

This document lists the planning and governance documents
to support the new base-zero roadmap. Each document is described
by title, function, and a one-line content summary.

## Proposed Document Set

### 1. [ROADMAP](01_TIMELINE.md)

**Function:** Canonical, user-facing roadmap for the project.
**Content:** High-level phases, objectives, non-goals, and decision checkpoints from v0.28.7.post14 onward.

---

### 2. [PLANNING_TIMELINE](01_TIMELINE.md)

**Function:** Internal planning reference aligned with the roadmap.
**Content:** Phase-by-phase timeline with dates, scope boundaries, buffers, and review gates.

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
- Document 12 is **non-binding by design** and must not leak into implementation work without approval.
