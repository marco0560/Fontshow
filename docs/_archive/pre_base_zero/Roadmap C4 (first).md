# Archived after base-zero planning (v0.28.7.post14)

# Fontshow Roadmap (post-0.28.7.post9)

[FACT] Current version: 0.28.7.post9
[FACT] This roadmap is derived from: `Fontshow_raw_list.txt`, the project snapshot `.zip`, and exported `issues.json` / `milestones_plan.json`.

## Guiding goals

- [PROPOSAL] Stabilize the pipeline contracts (schema, semantics, warnings, exit codes) before adding new enrichment logic.
- [PROPOSAL] Make diagnostics first-class (structured logging + explainability) so complex font behavior can be debugged reliably.
- [PROPOSAL] Keep platform-dependent behavior explicit and testable (markers + documented support matrix).

## Milestones

### 0.29.0 — C5.X Refinements (Languages / Charset / Logging)

Focus:
- [FACT] Dual-field language strategy (`coverage.languages_raw` vs `coverage.languages`) — GitHub #31.
- [FACT] Charset diagnostics and readability — GitHub #29, #30.
- [FACT] Close (or explicitly defer) logging-spec gaps — GitHub #26.

Deliverables:
- [PROPOSAL] Reduced validation noise on Gentoo runs.
- [PROPOSAL] Clear contracts for raw vs normalized language data.
- [PROPOSAL] Actionable, documented observability expectations.

### 0.30.0 — C7 Testing & Validation (Evidence + Robustness)

Focus:
- [FACT] Manual testing evidence and documentation — GitHub #8, #1.
- [FACT] Create-catalog / LaTeX debugging and robustness — GitHub #4, #5.
- [PROPOSAL] Add `.coveragerc` aligned with the documented coverage strategy.

Deliverables:
- [PROPOSAL] A reproducible manual-test protocol script.
- [PROPOSAL] Markers separating unit vs platform-dependent tests.
- [PROPOSAL] A small suite of LuaLaTeX robustness tests.

### 0.31.0 — C6 Orchestration & CLI UX (Unified entrypoints)

Focus:
- [FACT] Packaging & CLI UX — GitHub #9.
- [FACT] CLI consistency improvements requested in the raw list (format, explainability, exit codes).

Deliverables:
- [PROPOSAL] Unified `fontshow dump|parse|catalog|preflight|validate` entrypoints.
- [PROPOSAL] Preflight: `--format=json`, `--only-errors`, `--explain`.
- [PROPOSAL] A contributor-facing checklist for adding new CLI commands.

### 0.32.0 — Charset-aware Enrichment (Controlled feature evolution)

Focus:
- [FACT] Charset-aware enrichment proposal — GitHub #27.

Deliverables:
- [PROPOSAL] Explicit and documented precedence rules between charset-derived signals and Unicode/fontTools-derived signals.
- [PROPOSAL] Tests and structured diagnostics guarding against silent semantic changes.

### 0.33.0 — C8 CI & Automation (Stability + Reproducibility)

Focus:
- [FACT] CI & Automation ideas — GitHub #12.

Deliverables:
- [PROPOSAL] A CI split between fast checks and optional heavier workflows.
- [PROPOSAL] Schema regression tests with minimal, versioned sample inventories.
- [PROPOSAL] Docs build validation as a first-class CI signal.

### 2.0.0-alpha — Pluggable Backends (v2.x.y Objectives)

Focus:
- [FACT] Pluggable backend architecture — GitHub #25.

Deliverables:
- [PROPOSAL] Backend interface and Linux/fontconfig backend extracted.
- [PROPOSAL] Scaffolds for Windows-native and macOS CoreText discovery (no promise of full support yet).

## Backlog themes (kept intentionally short)

- [PROPOSAL] **Contracts first:** schema, semantics, warning codes, exit codes.
- [PROPOSAL] **Observability:** structured logs, explainable inference, reproducible diagnostics.
- [PROPOSAL] **Portability:** support matrix, platform evidence, explicit backends.
- [PROPOSAL] **Contributor experience:** clear docs, checklists, predictable patterns.

## Working agreements

- [PROPOSAL] Every new behavior MUST be documented (decision note or docs page), observable (structured log), and covered by tests.
- [PROPOSAL] Prefer incremental C-steps for enrichment (small, reviewable slices).
