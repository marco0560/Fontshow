# ISSUE_MODEL.md

## Fontshow — GitHub Issue Model

**Current version:** v0.28.7.post14
**Applies to:** All issues created after base-zero planning

---

## Purpose

This document defines what a **GitHub issue** means in the Fontshow project.

It establishes:
- the required structure of an issue,
- sizing and scope constraints,
- lifecycle states,
- and the relationship between issues, milestones, and sessions.

This document is **normative**: all issues MUST conform to this model.

---

## What an Issue Is

In Fontshow, an issue represents:

- a **single, session-sized unit of work**,
- executable within one focused development session,
- producing a **clearly verifiable outcome**.

An issue is the **atomic planning unit** above commits
and below milestones.

---

## Session-Sized Definition

An issue MUST be:

- reasonably completable in **one working session**,
- self-contained,
- testable or verifiable in isolation.

A “session” is defined as:
- a contiguous block of focused work,
- without relying on unfinished future issues.

If work exceeds a single session, the issue MUST be split.

---

## Issue Categories

Issues SHOULD be categorized using consistent labels.
Typical categories include:

- `stabilization`
- `testing`
- `docs`
- `cli`
- `pipeline`
- `governance`
- `design-spike`

Labels are descriptive, not contractual, but SHOULD be applied consistently.

---

## Required Issue Structure

Every issue MUST include:

### 1. Title
- Short, specific, action-oriented.
- Avoid vague wording such as “improve” or “refactor” without context.

### 2. Context
- Why this issue exists.
- What problem it addresses.

### 3. Scope
- What is included.
- What is explicitly excluded.

### 4. Acceptance Criteria
- Concrete, verifiable conditions for completion.
- Prefer observable outcomes over internal implementation details.

### 5. References (if applicable)
- Links to related issues, documents, or commits.

---

## Scope Constraints

An issue MUST NOT:

- span multiple milestones,
- introduce unrelated changes,
- silently expand scope during implementation.

Scope changes require:
- explicit documentation,
- and possible issue splitting.

---

## Issue Lifecycle

1. **Proposed**
   - Drafted but not yet scheduled.

2. **Scheduled**
   - Assigned to a milestone.

3. **In Progress**
   - Actively worked on.

4. **Blocked**
   - Cannot proceed due to an external dependency.

5. **Completed**
   - Acceptance criteria met.

6. **Deferred**
   - Explicitly postponed and removed from the milestone.

---

## Relationship to Milestones

- Every active issue MUST belong to exactly one milestone.
- Issues MUST NOT be shared across milestones.
- Closing a milestone with open issues is not allowed.

---

## Relationship to Commits

- An issue MAY be resolved by:
  - one commit, or
  - a small, coherent sequence of commits.
- Commits SHOULD reference the issue where appropriate.
- Commits MUST NOT bundle multiple unrelated issues.

---

## Anti-Patterns

The following are explicitly discouraged:

- “Umbrella” issues that hide multiple tasks.
- Issues that exist only as reminders.
- Issues that require speculative future decisions to complete.

Such items belong in planning documents, not in the issue tracker.

---

## Status

This issue model is **active** and mandatory for all GitHub issues
created after v0.28.7.post14.
