# Decision 0001 — Planning System Formalization

**Status:** Accepted
**Date:** 2026-01-14

## Context

Fontshow reached a level of technical and organizational complexity where
ad-hoc planning artifacts (roadmaps, issue drafts, action lists) were no
longer sufficient to ensure clarity, continuity, and governance.

Multiple planning-related documents existed, partially overlapping and
spread across iterations, making it difficult to:

- reconstruct intent and rationale
- align GitHub issues and milestones
- onboard contributors consistently

## Decision

We adopt a **formal, version-controlled planning system** stored directly
in the repository under `docs/planning/`, composed of a fixed, canonical
document set.

Additionally, we introduce a **Decision Records system** under
`docs/decisions/`, with one immutable file per decision.

Key points:

- Planning documents define *what* and *when*
- Decision records capture *why*
- Planning documents may evolve
- Decision records are append-only and immutable once accepted

## Consequences

### Positive

- Clear separation between planning and rationale
- Strong historical traceability
- Improved alignment between documentation, issues, and milestones
- Reduced ambiguity during refactoring and long-term evolution

### Trade-offs

- Slightly higher upfront documentation discipline
- Need to consciously decide when a change requires a new decision record

## Follow-ups

- Align GitHub milestones and issues with the planning documents
- Update documentation navigation to expose planning and decisions clearly
- Introduce `planning` as a first-class commit scope
