# Archived after base-zero planning (v0.28.7.post14)

# Document Set Accompanying Note
Fontshow Roadmap & Planning Artifacts

## Executive Summary

This document explains **how to read, use, and interpret** the set of planning
and roadmap documents produced during the Fontshow roadmap refactoring effort.

The document set represents a **progressive refinement process**:
- starting from a large, unstructured raw backlog,
- moving through deduplication and reality checks against the codebase,
- and culminating in a **concrete, executable plan** with milestones, issues,
  and session-level execution checklists.

Not all intermediate artifacts are meant to be kept as long-term references.
This note clarifies:
- which documents are **authoritative**,
- which are **historical or transitional**,
- and how they should be used together by maintainers and contributors.

---

## Purpose of the document set

The goals of this document set are to:

- provide a **realistic, code-aware roadmap**,
- reduce ambiguity between ideas, issues, and executable work,
- enable **session-sized, trackable development**,
- preserve architectural intent while avoiding speculative planning.

The documents are intentionally conservative and contract-driven.

---

## Overview of provided documents

### 1. Deduplicated & Grouped Master List (Point A)

**Role**
- Conceptual consolidation of all ideas from the original raw list.
- Grouped by architectural area.
- Prioritized (P1 / P2 / P3).

**How to use**
- As a **conceptual map** of the problem space.
- To understand *what exists* and *why it matters*.
- As a reference when evaluating future ideas.

**What NOT to use it for**
- Do NOT treat it as a task list.
- Do NOT track progress directly on this list.

**Status**
- Informational.
- Superseded operationally by Point B and later artifacts.

---

### 2. Filtered & Status-Aware Master List (Point B)

**Role**
- Reality-checked version of Point A.
- Explicitly removes items already implemented.
- Marks remaining items as:
  - PARTIALLY IMPLEMENTED
  - NOT IMPLEMENTED

**How to use**
- As the **bridge** between ideas and planning.
- To justify why certain items appear in milestones and issues.
- To explain scope decisions to contributors.

**What NOT to use it for**
- Do NOT use it for day-to-day execution.
- Do NOT open GitHub issues directly from this list.

**Status**
- Transitional but important.
- Superseded by C.1–C.4 for execution.

---

### 3. Atomic Action List (C.1)

**Role**
- The **atomic source of truth** for work items.
- Each action is:
  - minimal,
  - unambiguous,
  - mappable to issues and commits.

**How to use**
- As the internal backlog.
- For estimating effort.
- For checking coverage of roadmap vs implementation.

**What NOT to use it for**
- Do NOT expose directly to GitHub users.
- Do NOT treat items as milestones.

**Status**
- Authoritative at the planning level.

---

### 4. GitHub Issues (C.2 + gh script)

**Role**
- Public-facing, session-sized work units.
- Designed to be solvable in one development session.
- Aligned with milestones.

**How to use**
- These are the **only items** that should be tracked in GitHub Issues.
- Use the provided `gh` script to recreate them deterministically.
- Close issues independently, without implicit coupling.

**What NOT to use**
- Do NOT create additional ad-hoc issues that duplicate atomic actions.
- Do NOT overload issues with multi-milestone scope.

**Status**
- Authoritative for execution tracking.

---

### 5. Milestones & Issue Mapping (C.3)

**Role**
- Defines **why** issues are grouped together.
- Makes sequencing and dependencies explicit.
- Keeps milestones small and closable.

**How to use**
- As the planning reference for releases.
- To decide what *not* to include in a milestone.
- To evaluate readiness for release.
