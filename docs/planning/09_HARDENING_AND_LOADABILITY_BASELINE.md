# 09_HARDENING_AND_LOADABILITY_BASELINE.md

## Fontshow — Hardening & Loadability Baseline (Pre-Qt)

**Baseline:** base-zero planning
**Scope:** planning contract document
**Purpose:** define the current hardening phase and the stabilization baseline required before Qt discovery work

---

## Purpose

This document defines the project’s current hardening phase focused on:

- improving maintainability without architectural churn
- eliminating known LaTeX/catalog failure modes
- introducing deterministic LuaLaTeX loadability persistence in the inventory
- enabling reproducible diagnostics (discovery vs loadable)
- establishing a stable baseline prior to any Qt discovery branch work

This is a planning document (scope and sequencing), not an implementation guide.

---

## Background (Observed Failure Classes)

Recent runs identified that catalog generation can fail for reasons that are not related to discovery quality:

- **subset-empty failures** when specimen text contains glyphs not present in the font
- **name-based loading fragility** (`\fontspec{<face>}`) leading to `.fontspec` lookup and shape resolution aborts
- mismatch between “fonts discovered” and “fonts loadable by LuaLaTeX” depending on runtime environment

Therefore, discovery improvements (including Qt) do not replace robustness work in the rendering pipeline.

---

## Phase Objectives

### O1 — Procedural modularity improvement (refactoring)

Isolate layers without changing behavior:

- discovery
- path/face resolution
- rendering

No paradigm change. No OOP introduction.

### O2 — Rendering robustness (catalog must not abort)

Introduce fixes that ensure catalog generation cannot fail due to:

- subset-empty conditions (specimen mismatch)
- fragile name-based resolution

### O3 — Deterministic LuaLaTeX loadability persistence

Persist whether each font is loadable by LuaLaTeX in the inventory, together with global runtime metadata.

### O4 — Deterministic diagnostics (discovery vs loadable)

Enable reproducible extraction of:

- all discovered fonts (human-readable names)
- LuaLaTeX-loadable fonts (human-readable names)
- diff between the two

### O5 — Stabilization baseline gate before Qt

Qt discovery work is allowed only after the baseline defined below is satisfied.

---

## Deliverables (Planning Level)

### D1 — Refactoring baseline (no behavior change)

- clear separation of discovery, resolution, rendering entry points
- stable data contract used between layers

### D2 — Specimen strategy that prevents subset-empty

A deterministic specimen selection strategy that guarantees at least one renderable glyph per font.

### D3 — Path-first loading strategy

Prefer path-based font loading for robustness; keep safe fallback for cases where path is unavailable.

### D4 — Loadability persistence in inventory + runtime fingerprint

Inventory must include:

- per-font boolean flag: `lualatex_loadable`
- global metadata indicating loadability was checked and under which runtime:

  - engine/version identifier
  - luaotfload identifier (if available)
  - runtime fingerprint capturing relevant runtime/config state

### D5 — Deterministic lists and diff

Provide scripts or commands that, from the inventory, can produce:

- discovery list (human-readable)
- loadable list (human-readable)
- diff (discovery minus loadable)

---

## Runtime Fingerprint (Planning Contract)

The runtime fingerprint must:

- be deterministic
- change when the LuaLaTeX environment relevant to loading changes
- allow `create-catalog` to detect whether persisted loadability is valid

When fingerprint mismatch is detected, `create-catalog` must fall back to performing loadability checks at runtime.

---

## Non-Goals (Explicit)

This phase does NOT include:

- Qt discovery implementation (only preparation)
- GUI development
- performance optimization work
- large-scale refactors unrelated to the objectives
- shifting the codebase to OOP (unless future GUI requires it)

---

## Stabilization Baseline (Pre-Qt Gate)

The baseline is considered achieved when:

- catalog generation cannot abort due to subset-empty failures
- catalog generation cannot abort due to `.fontspec` name-resolution fragility
- persisted loadability is present and validated by runtime fingerprint
- discovery vs loadable diagnostics are deterministic and reproducible
- tests remain green and behavior is deterministic for the same environment

Only after this gate is met, Qt discovery can be developed in a dedicated branch.

---

## Relationship With Timeline and Other Planning Docs

- This document refines the LaTeX/catalog robustness planning described in `01_TIMELINE.md`.
- It must remain consistent with:
  - `02_PHASES.md` (allowed work / non-goals)
  - `08_STABILIZATION_SCOPE.md` (stabilization contract)
  - `10_PIPELINE_ROBUSTNESS.md` (resilience expectations)

---

End of document.
