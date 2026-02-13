# 02_PHASES.md

## Fontshow — Planning Phases Definition

**Baseline:** base-zero planning
**Effective from:** v0.28.7.post14

---

## Purpose

This document defines the **planning phases** used by the Fontshow project.

Phases describe:

- *what kind of work is allowed*,
- *what outcomes are expected*,
- *what is explicitly out of scope*.

Phases are **conceptual**.
They do **not** define dates, durations, or deadlines.

Temporal information lives exclusively in [`01_TIMELINE.md`](01_TIMELINE.md).

---

## Phase 0 — Baseline & Tooling

### Objective Phase 0

Establish a stable and shared baseline for planning, tooling, and development environment.

### In scope Phase 0

- Planning normalization
- Tooling validation
- Local development setup
- Documentation baseline
- Archival of superseded materials

### Out of scope Phase 0

- Feature development
- Refactors unrelated to tooling or planning
- User-facing changes

### Exit criteria Phase 0

- Canonical planning documents established
- Development environment reproducible
- Legacy planning artifacts archived

---

## Phase 1 — Stabilization

### Objective Phase 1

Make existing behavior explicit, reliable, and documented.

### In scope Phase 1

- Formalization of implicit contracts
- Alignment between code, tests, and documentation
- Bug fixes that restore intended behavior

### Out of scope Phase 1

- New features
- Architectural redesign
- Performance optimization beyond correctness

### Exit criteria Phase 1

- Stabilization issues closed or explicitly deferred
- Behavioral contracts documented and enforced

---

## Phase 2 — Testing Strategy Consolidation

### Objective Phase 2

Ensure deterministic and meaningful testing across environments.

### In scope Phase 2

- Classification of tests (unit vs integration)
- Isolation of environment-dependent tests
- CI-safe defaults

## Hardening and Stabilization-Oriented Work

The project includes a phase focused on strengthening determinism, robustness, and maintainability without altering the procedural architecture or introducing new features.

This phase is characterized by:

- elimination of known rendering and loading failure modes,
- deterministic LuaLaTeX loadability validation and persistence,
- strengthening of reproducibility guarantees,
- preparation of a stable baseline before any discovery backend transition (e.g. Qt).

### Allowed Work in this Phase

The following categories of work are explicitly allowed:

- Refactoring aimed at **clearer separation of existing layers** (discovery, resolution, rendering) without changing behavior.
- Robustness improvements in the rendering pipeline to prevent catalog aborts (subset-empty, fragile loading, environment-dependent failures).
- Introduction of deterministic mechanisms such as loadability persistence and runtime fingerprinting.
- Improvements in diagnostics and reproducibility (e.g. deterministic extraction of discovery vs loadable fonts).
- Code quality hardening that improves maintainability and prevents hidden bugs, including:
  - progressive static analysis hardening,
  - gradual typing where it clarifies contracts,
  - documentation and docstring audits where they improve understanding of invariants and behavior.

### Explicit Non-Goals

The following are **not** goals of this phase:

- Architectural paradigm changes (the project remains procedural).
- Introduction of GUI or user-facing feature expansion.
- Performance optimization unrelated to robustness or determinism.
- Opportunistic or large-scale refactors not directly supporting stabilization goals.
- Introduction of new discovery backends (e.g. Qt) before the stabilization baseline is reached.

### Stabilization Gate

Completion of this phase is defined by achieving a deterministic and reproducible baseline in which:

- catalog generation cannot abort due to subset-empty or loadability-related failures,
- loadability persistence is validated against runtime fingerprint,
- behavior is reproducible for identical environments,
- no known unresolved rendering failure classes remain.

Only after this gate is satisfied can work on alternative discovery backends proceed.

### Out of scope Phase 2

- New testing frameworks
- Coverage inflation without semantic value

### Exit criteria Phase 2

- Clear test taxonomy
- Predictable CI behavior
- Coverage aligned with contracts

---

## Phase 3 — Pipeline Robustness

### Objective Phase 3

Increase resilience and diagnosability of processing pipelines.

### In scope Phase 3

- Failure classification
- Error reporting improvements
- Partial failure survivability

### Out of scope Phase 3

- New pipeline stages
- Major performance rework

### Exit criteria Phase 3

- Documented failure modes
- Actionable diagnostics
- Stable pipeline behavior

---

## Phase 4 — CLI Contracts

### Objective Phase 4

Define and enforce stable CLI behavior.

### In scope Phase 4

- Exit code semantics
- Error handling guarantees
- Output consistency

### Out of scope Phase 4

- New CLI commands
- Breaking changes without explicit migration

### Exit criteria Phase 4

- CLI contract documented
- CLI behavior covered by tests

---

## Phase 5 — Charset-Aware Enrichment

### Objective Phase 5

Clarify scope and limits of charset-related enrichment.

### In scope Phase 5

- Definition of boundaries and non-goals
- Observability of charset behavior

### Out of scope Phase 5

- Broad Unicode feature expansion
- Heuristic-heavy inference changes

### Exit criteria Phase 5

- Charset behavior documented
- Observability in place

---

## Phase 6 — Governance & Documentation

### Objective Phase 6

Consolidate governance rules and contributor guidance.

### In scope Phase 6

- Decision records
- Contribution guidelines
- API boundary clarification

### Out of scope Phase 6

- Enforcement tooling
- Process-heavy bureaucracy

### Exit criteria Phase 6

- Governance model documented
- Contributor workflow clarified

---

## Phase 7 — v2 Design Spike

### Objective Phase 7

Explore future architectural directions without commitment.

### In scope Phase 7

- Design exploration
- Risk identification
- Go / no-go evaluation

### Out of scope Phase 7

- Implementation
- Breaking changes
- Migration plans

### Exit criteria Phase 7

- Documented findings
- Explicit decision recorded

---

## Relationship to Other Planning Documents

- **Timeline:** `01_TIMELINE.md`
- **Atomic actions:** `05_ATOMIC_ACTION_LIST.md`
- **Issues synthesis:** `06_ISSUE_BACKLOG_SYNTHESIS.md`

---

## Status

This document is **normative** for planning and phase classification.
