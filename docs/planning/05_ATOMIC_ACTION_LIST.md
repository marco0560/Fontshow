# ATOMIC_ACTION_LIST.md

## Fontshow — Atomic Action List

**Current version:** v0.28.7.post14
**Planning level:** Lowest (pre-issue)

---

## Purpose

This document enumerates **atomic actions** for the Fontshow project.

An atomic action is:
- the smallest meaningful unit of planned work,
- below the level of a GitHub issue,
- directly traceable to code, tests, or documentation changes.

This list serves as:
- a **planning substrate**,
- a **decomposition aid** for issues,
- and a **traceability anchor** during execution.

Atomic actions are **not** tracked individually on GitHub.

---

## What an Atomic Action Is

An atomic action represents:

- a **single, concrete change**,
- affecting a **specific file or tightly scoped set of files**,
- producing an observable effect.

Examples:
- “Add explicit exit code mapping to preflight CLI”
- “Split unit vs integration markers in pytest config”
- “Document failure isolation rules in pipeline docs”

---

## What an Atomic Action Is Not

An atomic action is **not**:

- a development session,
- a GitHub issue,
- a milestone,
- a vague intention (“clean up code”).

---

## Action Identification

Each atomic action is identified by:

```
A<number>
```

Numbering is **monotonic** and preserved even if actions are later removed.

---

## Action Categories

Atomic actions SHOULD be grouped by intent, such as:

- Planning
- Tooling
- Stabilization
- Testing
- CLI
- Pipeline
- Documentation
- Governance
- Design exploration

Categories are organizational only.

---

## Atomic Action List

### Planning & Tooling

- **A001** — Freeze existing planning artifacts as historical references
- **A002** — Audit current codebase, tests, and documentation state
- **A003** — Validate Python environment reproducibility
- **A004** — Validate pre-commit and git hook behavior
- **A005** — Validate Node and semantic-release preview setup

---

### Stabilization

- **A010** — Identify implicit behavioral contracts relied upon by tests
- **A011** — Document existing CLI exit code assumptions
- **A012** — Remove or reclassify obsolete refinements

---

### Testing

- **A020** — Classify existing tests as unit or integration
- **A021** — Isolate environment-dependent tests
- **A022** — Define CI-safe test defaults

---

### Pipeline Robustness

- **A030** — Identify single-font failure points in catalog generation
- **A031** — Add diagnostics for LaTeX-related failures
- **A032** — Document reproducibility steps for catalog generation

---

### CLI Contracts

- **A040** — Enumerate CLI commands and exit codes
- **A041** — Define machine-readable output expectations
- **A042** — Add regression tests for CLI exit behavior

---

### Charset-Aware Enrichment

- **A050** — Survey existing charset decoding logic
- **A051** — Define non-goals for charset enrichment
- **A052** — Add observability hooks for charset processing

---

### Governance & Documentation

- **A060** — Define public vs internal API boundaries
- **A061** — Document decision-record practices
- **A062** — Improve documentation navigation structure

---

### Design Exploration

- **A070** — Identify candidate pluggable backend boundaries
- **A071** — Draft interface sketches for v2 exploration
- **A072** — Record risks and unknowns for v2.x.y

---

## Maintenance Rules

- Atomic actions MAY be added as understanding improves.
- Atomic actions MUST NOT be silently removed.
- Changes to this list should preserve numbering and traceability.

---

## Status

This atomic action list is **active** and forms the basis
for issue decomposition and execution planning.
