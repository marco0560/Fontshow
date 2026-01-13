# ROADMAP.md

## Archived after base-zero planning (v0.28.7.post14)

## Fontshow — Project Roadmap

**Current version:** v0.28.7.post14
**Roadmap type:** Base-zero (supersedes all previous plans)

---

## Purpose

This roadmap describes the planned evolution of Fontshow starting from
v0.28.7.post14. It replaces all earlier milestone plans and timelines.

The roadmap focuses on:

- Stability and correctness first
- Explicit contracts and guarantees
- Controlled, observable feature evolution
- Long-term maintainability

This document is **user-facing** and intentionally high-level.
Implementation details are tracked in internal planning documents.

---

## Guiding Principles

- **Stabilize before extending**
  New features are introduced only after the existing system is robust,
  well-tested, and well-documented.

- **Explicit contracts**
  Behaviors relied upon by users, tests, and automation must be documented
  and enforced.

- **Environment-aware but deterministic**
  The project must behave consistently across supported environments,
  with clear separation between deterministic logic and environment-dependent checks.

- **Incremental evolution**
  Large features are decomposed into observable, reviewable steps.

---

## Roadmap Phases Overview

### Phase 0 — Re-baseline, tooling & environment setup

Establish a clean planning baseline and reproducible development environment.
No functional changes.

### Phase 1 — Stabilization sprint

Reduce friction and formalize existing behavior.
Optional stabilization release candidate.

### Phase 2 — Testing strategy & coverage alignment

Define and enforce a clear testing model with deterministic CI behavior.

### Phase 3 — LaTeX & catalog robustness

Improve pipeline survivability and diagnostics in real-world conditions.

### Phase 4 — CLI UX & exit code contracts

Stabilize CLI semantics and guarantees for both humans and automation.

### Phase 5 — Charset-aware enrichment

Introduce charset decoding and enrichment in controlled, incremental steps.

### Phase 6 — Governance & contributor experience

Improve documentation structure, onboarding, and long-term maintainability.

### Phase 7 — v2.x.y design spike (non-binding)

Explore future architecture options without implementation commitment.

---

## What This Roadmap Is *Not*

- It is **not** a promise of specific release dates.
- It is **not** a list of GitHub issues.
- It is **not** a feature wish list.

Detailed planning, issue breakdown, and execution tracking are handled
in dedicated planning documents.

---

## Change Policy

This roadmap is a **living document**, but:

- Changes must be explicit and justified.
- Scope expansions require review.
- Major reordering requires a planning checkpoint.

Historical roadmap versions should be preserved for reference.

---

## Status

This roadmap is **active** and reflects the approved base-zero plan
as of v0.28.7.post14.
