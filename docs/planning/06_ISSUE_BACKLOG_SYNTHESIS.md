# ISSUE_BACKLOG_SYNTHESIS.md

## Fontshow — Issue Backlog Synthesis

**Current version:** v0.28.7.post14
**Planning level:** Issue composition (post-atomic, pre-GitHub)

---

## Purpose

This document defines how **atomic actions** are grouped into
**session-sized GitHub issues**.

It acts as a bridge between:

- low-level atomic planning (`ATOMIC_ACTION_LIST.md`),
- and executable GitHub issues (`ISSUE_MODEL.md`).

This document is **normative** for issue composition.

---

## Synthesis Principles

Issue synthesis follows these rules:

1. **Session-sized**
   - An issue MUST be completable in a single focused session.

2. **Single intent**
   - All atomic actions in an issue MUST serve one clear objective.

3. **Minimal coupling**
   - Atomic actions with unrelated side-effects MUST NOT be grouped.

4. **Traceability**
   - Every issue MUST list the atomic actions it covers.

---

## Issue Identification

Issues are identified internally as:

```txt
I<number>
```

This identifier is used during planning only.
GitHub issue numbers are assigned later.

---

## Synthesis by Phase

### Phase 0 — Re-baseline & Tooling

- **I001 — Establish planning baseline**
  - Covers: A001, A002
  - Outcome: Project state understood and documented.

- **I002 — Validate development tooling**
  - Covers: A003, A004, A005
  - Outcome: Reproducible local development setup.

---

### Phase 1 — Stabilization

- **I010 — Formalize existing behavioral contracts**
  - Covers: A010, A011
  - Outcome: Implicit assumptions made explicit.

- **I011 — Clean up obsolete refinements**
  - Covers: A012
  - Outcome: Reduced planning and issue noise.

---

### Phase 2 — Testing Strategy

- **I020 — Classify test suite**
  - Covers: A020
  - Outcome: Tests clearly categorized.

- **I021 — Isolate environment-dependent tests**
  - Covers: A021, A022
  - Outcome: Deterministic CI behavior.

---

### Phase 3 — Pipeline Robustness

- **I030 — Identify and document pipeline failure points**
  - Covers: A030, A032
  - Outcome: Known failure modes documented.

- **I031 — Improve pipeline diagnostics**
  - Covers: A031
  - Outcome: Actionable error reporting.

---

### Phase 4 — CLI Contracts

- **I040 — Define CLI exit code contract**
  - Covers: A040
  - Outcome: Stable exit semantics.

- **I041 — Validate CLI output guarantees**
  - Covers: A041, A042
  - Outcome: CLI behavior enforceable by tests.

---

### Phase 5 — Charset-Aware Enrichment

- **I050 — Define charset enrichment boundaries**
  - Covers: A050, A051
  - Outcome: Feature scope constrained and explicit.

- **I051 — Add charset observability**
  - Covers: A052
  - Outcome: Feature behavior observable and testable.

---

### Phase 6 — Governance & Documentation

- **I060 — Define API boundaries**
  - Covers: A060
  - Outcome: Public vs internal APIs clarified.

- **I061 — Establish governance practices**
  - Covers: A061, A062
  - Outcome: Contribution and decision processes documented.

---

### Phase 7 — Design Spike

- **I070 — Explore v2 architecture boundaries**
  - Covers: A070, A071, A072
  - Outcome: Informed go / no-go decision.

---

## Rules for GitHub Issue Creation

When creating GitHub issues from this synthesis:

- One GitHub issue SHOULD map to exactly one `I<number>`.
- Atomic actions MUST be referenced in the issue body.
- Acceptance criteria MUST reflect the listed outcomes.

---

## Status

This synthesis is **active** and serves as the authoritative source
for generating GitHub issues and milestones.
