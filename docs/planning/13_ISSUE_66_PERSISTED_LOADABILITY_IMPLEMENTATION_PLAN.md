# Issue 66 - Persisted Loadability Implementation Plan

## Status

Status: active execution plan
Related issue: `#66`
Execution branch: `feat/catalog-persisted-loadability`

## Purpose

This document records the approved execution plan for Issue `#66`:

- persist LuaLaTeX loadability during `dump-fonts`
- consume persisted loadability in `create-catalog`
- remove the `create-catalog --validate-loadability` option and code path
- preserve deterministic fallback behavior when persisted loadability is
  absent or invalid
- update and review repository documentation before merge

This is an execution-tracking document, not a replacement for the
architectural rationale already recorded in ADR 0026.

## Scope

In scope:

- batched LuaLaTeX probing in `dump-fonts`
- runtime fingerprint generation and comparison
- persistence of per-font and inventory-level loadability metadata
- default persisted-loadability consumption in `create-catalog`
- deterministic reporting of unloadable fonts in generated catalog output
- deterministic tests covering persistence and fallback
- repository documentation updates and review before merge

Out of scope:

- unrelated refactors
- Qt discovery work
- GUI work
- broad inventory redesign beyond the active schema contract
- weakening deterministic test constraints

## Branch and Commit Policy

All work for Issue `#66` must be performed on the dedicated branch:

- `feat/catalog-persisted-loadability`

The branch must not be merged back to `main` until:

- all plan steps are marked complete
- documentation updates are complete and reviewed
- `pre-commit run --all-files` passes
- `pytest -q` passes

The intended commit structure is one commit per implementation step when
the repository can remain in a coherent state.

## Execution Workflow

Before each implementation step:

1. propose the concrete step plan
2. wait for explicit confirmation
3. execute only the confirmed step
4. update this document to reflect progress

## Planned Steps

### Step 1 - Planning artifact and branch setup

Goal:
Create the dedicated branch and add this execution-tracking document.

Deliverables:

- dedicated branch created
- implementation plan committed to the repository

### Step 2 - Remove `create-catalog --validate-loadability`

Goal:
Remove the CLI option and code path that treat runtime loadability
validation as an explicit opt-in behavior.

Deliverables:

- parser option removed
- runtime branch removed or replaced
- affected CLI tests updated

### Step 3 - Runtime fingerprint and persistence helpers

Goal:
Introduce the helper layer required to build, persist, and compare the
LuaLaTeX runtime fingerprint and related loadability metadata.

Deliverables:

- deterministic fingerprint helper(s)
- inventory/catalog access helpers for persisted loadability state
- test seams for deterministic probing behavior

### Step 4 - Batched loadability probing in `dump-fonts`

Goal:
Implement `dump-fonts` support for persisted LuaLaTeX loadability via
default batched probing with an opt-out flag.

Deliverables:

- `dump-fonts --no-loadability`
- batched TeX generation and execution
- deterministic attribution of probe results to font entries
- persisted per-font loadability fields
- persisted inventory-level validation metadata

### Step 5 - Persisted-loadability consumption in `create-catalog`

Goal:
Make `create-catalog` use persisted loadability by default and fall back
to runtime probing only when persisted data is absent or invalid.

Deliverables:

- persisted-first filtering behavior
- runtime-fallback path on fingerprint mismatch or missing data
- deterministic skip behavior for unloadable fonts

### Step 6 - Unloadable-font reporting in generated output

Goal:
Expose unloadable-font exclusions in generated catalog output rather
than only in logs.

Deliverables:

- stable unloadable count
- stable family/path listing
- stable reason summary when available

### Step 7 - Deterministic test coverage

Goal:
Cover the new persisted-loadability behavior without relying on a real
LaTeX installation.

Deliverables:

- `dump-fonts` persistence tests
- batch parser attribution tests
- fingerprint match/mismatch tests
- `create-catalog` behavior tests
- generated output reporting tests

Coverage assessment:

- evaluated surfaces from Steps 2-6:
  - `dump-fonts` default probing and `--no-loadability`
  - batched probing attribution
  - persisted metadata helper behavior
  - `parse-inventory` metadata preservation
  - persisted-first `create-catalog` filtering
  - runtime fallback on stale or missing persisted state
  - generated unloadable-font reporting
  - CLI completion / parser contract updates
  - schema/output invariants and deterministic output
- targeted verification suite executed successfully:

```bash
source .venv/bin/activate && pytest -q \
  tests/cli/test_dump-fonts.py \
  tests/cli/test_parse-inventory.py \
  tests/test_bash_completion.py \
  tests/test_dump_fonts_filtering.py \
  tests/test_dump_summary_skip_reporting.py \
  tests/test_unloadable_font_behavior.py \
  tests/test_dump_loadability.py \
  tests/test_inventory_loadability_helpers.py \
  tests/test_catalog_loadability.py \
  tests/test_catalog_document.py \
  tests/test_create_catalog_runtime.py \
  tests/test_deterministic_output.py \
  tests/test_output_schema_invariants.py \
  tests/schema/test_inventory_schema_validation.py \
  tests/schema/test_schema_validation.py \
  tests/schema/test_schema_validation_charset.py
```

Result:

- `83 passed`
- no additional deterministic test gaps were identified for the
  implemented behavior

### Step 8 - Repository documentation update and review

Goal:
Update and review repository documentation to match the implemented
behavior before merge.

Deliverables:

- command documentation updated
- planning/runtime docs updated where needed
- stale references to `--validate-loadability` removed

### Step 9 - Final validation and merge gate

Goal:
Run the required validation surface and verify the branch is ready for
merge.

Deliverables:

- `pre-commit run --all-files`
- `pytest -q`
- final checklist review

## Step Checklist

| Step | Title | Status | Notes |
| --- | --- | --- | --- |
| 1 | Planning artifact and branch setup | completed | Branch created and plan added |
| 2 | Remove `create-catalog --validate-loadability` | completed | CLI option and runtime branch removed |
| 3 | Runtime fingerprint and persistence helpers | completed | Fingerprint and v1.3 loadability helpers added |
| 4 | Batched loadability probing in `dump-fonts` | completed | Default probing with serial batching and `--no-loadability` opt-out |
| 5 | Persisted-loadability consumption in `create-catalog` | completed | Persisted-first filtering with deterministic runtime fallback |
| 6 | Unloadable-font reporting in generated output | completed | Generated catalog now includes deterministic exclusion reporting |
| 7 | Deterministic test coverage | completed | Coverage evaluated; targeted persisted-loadability suite passed (83 tests) |
| 8 | Repository documentation update and review | completed | Command docs updated and stale user-facing references removed |
| 9 | Final validation and merge gate | completed | `pre-commit run --all-files` and `pytest -q` both passed |

## Validation Contract

The required validation surface for closing the branch is:

```bash
pre-commit run --all-files
pytest -q
```

These checks must pass before merge readiness is declared.
