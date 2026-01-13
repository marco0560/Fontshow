# STABILIZATION_SCOPE.md

## Fontshow — Stabilization Phase Contract

**Current version:** v0.28.7.post14
**Applies to:** Phase 1 — Stabilization sprint

---

## Purpose

This document defines the **scope, rules, and acceptance criteria**
for the stabilization phase.

The stabilization phase exists to:
- reduce friction,
- formalize existing behavior,
- and prepare the codebase for controlled evolution.

This document is **normative** for all stabilization work.

---

## Definition of Stabilization

In Fontshow, **stabilization** means:

- making existing behavior **explicit and reliable**,
- removing ambiguity from contracts already relied upon,
- improving robustness **without expanding feature scope**.

Stabilization is about **correctness and clarity**, not innovation.

---

## In-Scope Work

The following types of work are explicitly allowed:

- Documenting implicit behavioral contracts.
- Fixing inconsistencies between code, tests, and documentation.
- Improving error handling where behavior already exists.
- Refactoring to make existing behavior reliable and testable.
- Removing or reclassifying obsolete or misleading functionality.

---

## Out-of-Scope Work

The following are explicitly **not allowed** during stabilization:

- Introducing new user-facing features.
- Expanding CLI command sets.
- Changing output formats without backward-compatibility handling.
- Large-scale architectural redesign.
- Performance optimizations unrelated to correctness.

Any work that violates these constraints MUST be deferred.

---

## Acceptance Criteria

Stabilization work is considered complete when:

- All stabilization issues in the milestone are closed or explicitly deferred.
- Documented behavior matches observed behavior.
- Tests reflect documented contracts.
- No “temporary” fixes remain undocumented.

Partial stabilization is not acceptable.

---

## Risk
