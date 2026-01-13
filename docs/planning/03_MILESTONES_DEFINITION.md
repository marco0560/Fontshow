# MILESTONES_DEFINITION.md

## Fontshow — Milestone Model and Semantics

**Current version:** v0.28.7.post14
**Applies to:** All milestones defined after base-zero planning

---

## Purpose

This document defines what a **milestone** means in the Fontshow project.

It establishes:

- a uniform milestone taxonomy,
- strict scope and sizing rules,
- completion criteria,
- and constraints on what milestones may contain.

This document is **normative**: deviations must be explicit and justified.

---

## What a Milestone Is

In Fontshow, a milestone is:

- a **time-bounded planning container**,
- aligned with a **single roadmap phase**,
- composed of **session-sized GitHub issues**,
- designed to deliver a **coherent, reviewable outcome**.

A milestone is **not**:

- a vague theme,
- an unbounded backlog,
- a placeholder for “future ideas”.

---

## Milestone Taxonomy

### Milestone Naming

Milestones MUST follow this format:

```txt
<version> — <short descriptive title>
```

Examples:

- `0.29.0 — Stabilization`
- `0.30.0 — Testing Alignment`
- `0.31.0 — Pipeline Robustness`

Rules:

- Version numbers reflect **intent**, not release promises.
- Patch or post-release suffixes are allowed only for corrective milestones
  (e.g. `0.29.1 — Stabilization Fixes`).

---

## Scope Rules

A milestone MUST:

- Map to **exactly one roadmap phase**.
- Have a **clearly stated objective**.
- Contain only issues that directly contribute to that objective.

A milestone MUST NOT:

- Span multiple roadmap phases.
- Mix stabilization and feature expansion.
- Serve as a dumping ground for unrelated issues.

---

## Size Constraints

A milestone SHOULD:

- Represent **2–4 weeks** of part-time work.
- Contain **3–10 session-sized issues**.

A milestone MUST NOT:

- Depend on unresolved future milestones.
- Contain issues that are themselves multi-session efforts.

If work exceeds these bounds, the milestone MUST be split.

---

## Completion Criteria

A milestone is considered **complete** when:

- All included issues are:
  - closed as completed, or
  - explicitly deferred and removed.
- All acceptance criteria defined at milestone creation are met.
- No “almost done” issues remain inside the milestone.

Partial completion is not allowed.

---

## Milestone Lifecycle

1. **Proposed**
   - Scope and objective defined.
   - Issues drafted but not yet committed.

2. **Active**
   - Issues accepted and work started.

3. **Frozen**
   - No new issues may be added.
   - Only completion or removal is allowed.

4. **Completed**
   - All criteria met.
   - Milestone closed.

5. **Archived**
   - Historical reference only.

---

## Relationship to Releases

- A milestone MAY result in a release.
- A release MAY include work from multiple milestones.
- Milestones MUST NOT be retroactively redefined to fit a release.

Release decisions are handled separately from milestone planning.

---

## Review and Change Policy

- Milestone definitions may evolve, but changes must:
  - be documented,
  - preserve backward traceability,
  - not invalidate completed milestones.

Historical milestone definitions must remain accessible.

---

## Status

This milestone model is **active** and mandatory for all planning
activities following v0.28.7.post14.
