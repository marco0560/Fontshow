# Catalog Artifact Hardening Implementation Plan

## Status

Status: active execution plan
Execution branch: `feat/catalog-artifact-hardening`
Primary roadmap issues: `#70`, `#59`
Supporting roadmap context: `milestones_plan.json`, `issues.json`

## Purpose

This document turns the current catalog artifact findings into an
execution plan against the repository codebase.

Primary goals:

- fix the Python-generated LaTeX defect that injects control bytes into
  non-Latin specimen blocks
- make default `create-catalog` output single-pass friendly and remove
  obsolete TeX-side bookkeeping
- add an opt-in indexed navigation mode aligned with Issue `#70`
- improve specimen usefulness without misrepresenting specialized fonts
- reduce PDF bulk and visual noise while preserving deterministic output

This is an execution document. It does not replace existing decisions or
issue text and must remain aligned with repository files and tests.

## Issue Map

### Issue `#70` - gate TOC and clickable navigation behind a flag

Planned outcomes mapped to this issue:

- new explicit navigation flag in `create-catalog`
- default output with no TOC and no end-of-document navigation tables
- removal of TeX-side `.working`, `.broken`, `.excluded` bookkeeping
- single-pass-friendly default output
- clickable navigation in indexed mode using stable anchors built from
  rendered catalog structure

Expected close condition:

- close when the new default/indexed split is implemented, tested, and
  documented

### Issue `#59` - create selective archives

Planned outcomes mapped to this issue:

- selection flags for script and language scoped output
- sort/group support needed for practical compact archives
- output reduction by reducing catalog scope before rendering

Expected close condition:

- close only when filtering and ordering behavior are implemented and
  documented

### Gap not covered by a current open issue

The following work is not cleanly covered by an existing roadmap issue
and should be tracked before merge if implemented beyond incidental bug
fixing:

- specimen-quality gating for low-information but technically valid
  specimens
- specialized-font rendering policy for symbol, icon, chess, and similar
  families
- compact visual-density controls beyond the basic navigation split

If this branch introduces those behaviors as first-class CLI or catalog
policy, create a dedicated issue before merge and reference it from the
ledger.

## Code Map

### CLI contract and orchestration

- `src/fontshow/cli/create_catalog.py`
  - add explicit navigation mode flag(s)
  - add script/language selection flag(s) for scoped archives
  - thread compact/indexed mode metadata into document generation

### Catalog assembly and rendering

- `src/fontshow/catalog/document.py`
  - fix non-Latin specimen rendering defect in `_render_font_entry`
  - add stable anchor generation for family and variant blocks
  - remove obsolete TeX-side logging emissions
  - split default compact output from opt-in indexed navigation output
  - add low-value specimen suppression and specialized-font handling

### Static LaTeX template fragments

- `src/fontshow/latex/templates.py`
  - remove legacy `\openout`, `\LogWorking`, `\LogBroken`,
    `\LogExcluded`, `\FileSec`, and unconditional `\tableofcontents`
  - add clean default front matter
  - add opt-in navigation fragments for indexed mode only

### Specimen generation and fallback policy

- `src/fontshow/inventory/specimens.py`
  - preserve deterministic fallback chain for primary specimens
  - extend policy only if needed for stronger low-quality rejection

### Shared specimen helpers / ontology-backed fallback

- `src/fontshow/common/specimens.py`
- `src/fontshow/ontology/language_tables.py`
  - authoritative predefined samples used when low-quality primary
    specimens need curated replacement

### Test surfaces

- `tests/cli/test_create-catalog.py`
- `tests/test_catalog_document.py`
- `tests/test_create_catalog_runtime.py`
- `tests/test_deterministic_output.py`
- `tests/test_artifact_hygiene.py`
- additional focused tests to be added as required by the implemented
  scope

## Verified Current Defects

These findings were verified from generated artifacts on this branch:

- `longtest.tex` contains injected ASCII control byte `0x08` before
  `egingroup` in many non-Latin blocks
- `longtest.log` shows repeated invalid-character and brace-balance
  errors originating from those emitted blocks
- default output still emits unconditional TOC and legacy auxiliary
  bookkeeping
- `.working`/`.broken` reporting duplicates information already decided
  in Python
- many rendered specimens are too short to be useful, especially for
  specialized fonts

## ADR Decision Gate

An ADR is not created immediately by default.

Create a new decision record only if implementation confirms one of the
following:

- the default catalog output contract changes in a way that should be
  treated as an architectural policy rather than an issue-level fix
- specialized-font specimen policy becomes a durable repository-wide
  rendering rule
- navigation/indexed mode introduces a stable long-term document model
  that should be recorded separately from issue `#70`

If triggered, create the ADR before merging the first commit that
depends on that policy and update `docs/decisions/index.md`.

## Branch and Commit Policy

All work for this effort must remain on:

- `feat/catalog-artifact-hardening`

Commit principle:

- commit often
- keep each commit atomic and reviewable
- use commit messages compliant with `.githooks/commit-msg.py`
- add `Closes: #<issue>` footers only in the commit that actually
  satisfies the issue acceptance criteria

## Execution Phases

### Step 1 - Branch, plan, and ledger baseline

Goal:
Create the execution branch, implementation plan, and execution ledger.

Deliverables:

- branch created
- plan committed
- ledger committed

### Step 2 - Fix the non-Latin LaTeX emission defect

Goal:
Remove the Python-generated rendering bug that injects control bytes and
causes runaway-group recovery in LuaLaTeX.

Primary files:

- `src/fontshow/catalog/document.py`
- `tests/test_catalog_document.py`
- `tests/test_deterministic_output.py`

Deliverables:

- no control-byte injection in emitted LaTeX
- targeted regression tests for the broken rendering branch
- deterministic output preserved

### Step 3 - Remove obsolete TeX-side bookkeeping from default output

Goal:
Implement the default-output side of Issue `#70`.

Primary files:

- `src/fontshow/latex/templates.py`
- `src/fontshow/catalog/document.py`
- `tests/test_catalog_document.py`
- `tests/test_artifact_hygiene.py`

Deliverables:

- no unconditional TOC
- no `.working`, `.broken`, `.excluded` generation in default mode
- no `\LogWorking` / `\LogBroken` / `\LogExcluded` / `\FileSec`
- single-pass-friendly default output

### Step 4 - Add opt-in indexed navigation mode

Goal:
Implement the indexed-mode side of Issue `#70`.

Primary files:

- `src/fontshow/cli/create_catalog.py`
- `src/fontshow/catalog/document.py`
- `src/fontshow/latex/templates.py`
- `tests/cli/test_create-catalog.py`
- `tests/test_catalog_document.py`

Deliverables:

- explicit CLI flag
- stable family or variant anchors
- clickable TOC in indexed mode
- clickable end index in indexed mode

### Step 5 - Add selective archive controls

Goal:
Implement Issue `#59` so the catalog can be made smaller before
rendering.

Primary files:

- `src/fontshow/cli/create_catalog.py`
- `src/fontshow/catalog/pipeline.py`
- `tests/cli/test_create-catalog.py`
- `tests/test_create_catalog_runtime.py`

Deliverables:

- script selection
- language selection
- deterministic sorting/grouping additions required by the issue

### Step 6 - Improve specimen usefulness without lying about specialized fonts

Goal:
Apply the agreed safer rule:

- use Fontshow’s predefined specimens when the current specimen is
  low-quality because it is invalid or mismatched
- do not replace specialized-font specimens with misleading normal-text
  samples

Primary files:

- `src/fontshow/catalog/document.py`
- `src/fontshow/inventory/specimens.py` if policy extension is needed
- `src/fontshow/common/specimens.py` only if fallback selection changes
- focused tests in `tests/test_catalog_document.py` and
  `tests/test_inventory_specimens.py`

Deliverables:

- low-information primary specimens either replaced by curated fallback
  or suppressed according to deterministic rules
- specialized fonts rendered with an explicit specialized policy
- no broadening of specimen semantics without tests

### Step 7 - Compact visual layout pass

Goal:
Reduce PDF size and visual clutter without compromising determinism.

Primary files:

- `src/fontshow/latex/templates.py`
- `src/fontshow/catalog/document.py`
- snapshot-style assertions in `tests/test_catalog_document.py`

Candidate changes:

- smaller metadata footprint
- tighter block spacing
- optional compact specimen sizing
- reduced repeated status noise

### Step 8 - ADR decision checkpoint

Goal:
Decide whether the implemented output-policy changes require a formal
decision record.

Deliverables:

- explicit ledger entry: `ADR not required` or `ADR created`
- decision index updated only if an ADR is added

### Step 9 - Final validation and issue closure pass

Goal:
Run the repository validation surface, verify issue closure criteria,
and prepare merge-ready commits.

Required validation:

```bash
pre-commit run --all-files
pytest -q
```

Deliverables:

- validation recorded in ledger
- closing commit(s) reference the correct issue numbers
- no unresolved plan items remain open without explanation

## Ledger

Execution status is tracked in:

- `docs/planning/15_CATALOG_ARTIFACT_HARDENING_EXECUTION_LEDGER.md`
