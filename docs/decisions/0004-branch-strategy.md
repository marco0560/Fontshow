# Decision 0004 — Branching Strategy Formalization

## Status

**Status:** Accepted
**Date:** 14/01/2026

## Context

With the introduction of a formal planning system (phases, milestones, atomic
actions, and issues), the project requires a clear and lightweight branching
strategy that:

- Preserves traceability between code, issues, and planning artifacts
- Scales from small incremental changes to larger integration efforts
- Avoids unnecessary process overhead
- Remains compatible with semantic-release and CI automation

The project is primarily developed by a small number of contributors, with a
strong emphasis on clarity, determinism, and reproducibility.

## Decision

The project adopts a **three-tier branching strategy**, with clearly separated
purposes:

### 1. Issue branches (default)

Branches created to implement a single GitHub issue.

#### Issue aming convention

```txt
issue/<issue-number>-short-description
```

#### Issue Rules*

- One issue per branch
- Regularly rebased or merged onto `main`
- Always merged via pull request (even for a single contributor)
- Primary unit of day-to-day development

This is the **default and mandatory** branching mode.

---

### 2. Milestone integration branches (optional)

Branches used to integrate multiple issue branches belonging to the same
milestone.

#### Milestone Naming convention

```txt
milestone/M1
milestone/M2
milestone/M3
```

#### Milestone Rules

- Used as temporary integration buffers
- Intended for stabilization and cross-issue validation
- May be merged into `main` once the milestone scope is complete
- Not required for every milestone

These branches are **optional but recommended** for M2 and later milestones.

---

### 3. Spike / phase branches (exploratory)

Branches used for experimentation, refactoring spikes, or exploratory design
work that is not yet tied to an approved issue.

#### Spike Naming convention

```txt
spike/<topic>
phase/<name>
```

#### Spile Rules

- No stability guarantees
- May be deleted without merging
- Must not be merged into `main` without:
  - an approved decision
  - or a corresponding GitHub issue

These branches explicitly support exploratory work without polluting the main
history.

## Consequences

- `main` remains stable and release-ready at all times
- Every functional change is traceable to a GitHub issue
- Larger integration efforts are isolated and controlled
- Exploratory work is clearly separated from committed roadmap work
- The branching model remains simple, explicit, and low-overhead

This strategy aligns branching with the planning model without introducing
phase- or milestone-level rigidity into day-to-day development.
