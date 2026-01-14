# Decision 0001 — Base-Zero Replanning and Governance Reset

**Status:** Accepted
**Date:** 2026-01-15
**Context version:** v0.28.7.post14

---

## Context

Over the course of the Fontshow project evolution, planning artifacts, milestones,
and GitHub issues accumulated organically across multiple development cycles.

This resulted in:

- Heterogeneous milestone naming and scope
- Partial overlap between roadmap, milestones, and issues
- Difficulty distinguishing legacy work from newly planned work
- Reduced clarity for contributors and maintainers

By version **v0.28.7.post14**, the existing planning model was no longer providing
sufficient governance guarantees for continued development.

---

## Decision

A **base-zero replanning** was performed with the following decisions:

1. The existing planning artifacts and GitHub milestones were declared **legacy**
   and formally archived.
2. A new planning framework was introduced under `docs/planning/`, including:
   - Timeline definition
   - Phase separation
   - Milestone model
   - Atomic action list
3. GitHub milestones were recreated **ex-novo**, based on the new planning model:
   - `M1 – Consolidation`
   - `M2 – Feature Hardening`
   - `M3 – Release Readiness`
4. Existing GitHub issues were audited and reassigned to the new milestones
   where still relevant.
5. A semantic distinction between issue origins was introduced via labels:
   - `legacy` — issues predating the base-zero replanning
   - `planning` — issues derived from the new planning framework
6. Future planning decisions will be documented as **individual decision records**
   under `docs/decisions/`.

This document represents the **formal transition point** between legacy planning
and the new governance model.

---

## Rationale

This approach was chosen to:

- Preserve historical context without constraining future development
- Restore a clear separation between governance (planning) and execution (issues)
- Improve GitHub readability and contributor onboarding
- Enable scalable and auditable decision tracking going forward

A single monolithic `decisions.md` file was deemed insufficient for long-term
maintainability at the current project maturity level.

---

## Consequences

- All legacy milestones are closed and archived.
- Planning artifacts prior to this decision are preserved under
  `docs/_archive/pre_base_zero/`.
- New work MUST originate from `docs/planning/` and be tracked via
  milestones and issues consistent with the new model.
- All future architectural or governance decisions SHOULD be documented
  as standalone files in `docs/decisions/`.

---

## Follow-ups

- Optionally introduce an index file for decisions (`docs/decisions/README.md`)
- Decide whether to freeze or repurpose the legacy `decisions.md` file
- Enforce decision references in future planning documents when applicable

---

## References

- `docs/planning/00_Planning_Document_Set.md`
- `docs/planning/01_TIMELINE.md`
- `docs/planning/03_MILESTONES_DEFINITION.md`
- GitHub milestones `M1`, `M2`, `M3`
- The completion of this decision is marked in the repository by the internal tag post-planning-v0.28.7.post14.
