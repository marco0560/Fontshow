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

Temporal information lives exclusively in `01_TIMELINE.md`.

---

## Phase 0 — Baseline & Tooling

### Objective
Establish a stable and shared baseline for planning, tooling, and development environment.

### In scope
- Planning normalization
- Tooling validation
- Local development setup
- Documentation baseline
- Archival of superseded materials

### Out of scope
- Feature development
- Refactors unrelated to tooling or planning
- User-facing changes

### Exit criteria
- Canonical planning documents established
- Development environment reproducible
- Legacy planning artifacts archived

---

## Phase 1 — Stabilization

### Objective
Make existing behavior explicit, reliable, and documented.

### In scope
- Formalization of implicit contracts
- Alignment between code, tests, and documentation
- Bug fixes that restore intended behavior

### Out of scope
- New features
- Architectural redesign
- Performance optimization beyond correctness

### Exit criteria
- Stabilization issues closed or explicitly deferred
- Behavioral contracts documented and enforced

---

## Phase 2 — Testing Strategy Consolidation

### Objective
Ensure deterministic and meaningful testing across environments.

### In scope
- Classification of tests (unit vs integration)
- Isolation of environment-dependent tests
- CI-safe defaults

### Out of scope
- New testing frameworks
- Coverage inflation without semantic value

### Exit criteria
- Clear test taxonomy
- Predictable CI behavior
- Coverage aligned with contracts

---

## Phase 3 — Pipeline Robustness

### Objective
Increase resilience and diagnosability of processing pipelines.

### In scope
- Failure classification
- Error reporting improvements
- Partial failure survivability

### Out of scope
- New pipeline stages
- Major performance rework

### Exit criteria
- Documented failure modes
- Actionable diagnostics
- Stable pipeline behavior

---

## Phase 4 — CLI Contracts

### Objective
Define and enforce stable CLI behavior.

### In scope
- Exit code semantics
- Error handling guarantees
- Output consistency

### Out of scope
- New CLI commands
- Breaking changes without explicit migration

### Exit criteria
- CLI contract documented
- CLI behavior covered by tests

---

## Phase 5 — Charset-Aware Enrichment

### Objective
Clarify scope and limits of charset-related enrichment.

### In scope
- Definition of boundaries and non-goals
- Observability of charset behavior

### Out of scope
- Broad Unicode feature expansion
- Heuristic-heavy inference changes

### Exit criteria
- Charset behavior documented
- Observability in place

---

## Phase 6 — Governance & Documentation

### Objective
Consolidate governance rules and contributor guidance.

### In scope
- Decision records
- Contribution guidelines
- API boundary clarification

### Out of scope
- Enforcement tooling
- Process-heavy bureaucracy

### Exit criteria
- Governance model documented
- Contributor workflow clarified

---

## Phase 7 — v2 Design Spike

### Objective
Explore future architectural directions without commitment.

### In scope
- Design exploration
- Risk identification
- Go / no-go evaluation

### Out of scope
- Implementation
- Breaking changes
- Migration plans

### Exit criteria
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
