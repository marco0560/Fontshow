# Catalog Artifact Hardening Execution Ledger

## Status

Status: active
Execution branch: `feat/catalog-artifact-hardening`
Implementation plan: `docs/planning/14_CATALOG_ARTIFACT_HARDENING_IMPLEMENTATION_PLAN.md`

## Ledger Rules

- Every significant step executed on this branch must be recorded here.
- Each entry must be updated when a step starts and when it completes.
- If scope changes, record the reason before implementing the change.
- If an ADR becomes necessary, record the trigger here before creating
  the ADR.
- If an issue is closed by a commit, record the commit and the issue
  number in the matching step entry.

## Step Ledger

### Step 1 - Branch, plan, and ledger baseline

Status: completed

Verified work:

- created branch `feat/catalog-artifact-hardening`
- added implementation plan
- added execution ledger

Artifacts:

- `docs/planning/14_CATALOG_ARTIFACT_HARDENING_IMPLEMENTATION_PLAN.md`
- `docs/planning/15_CATALOG_ARTIFACT_HARDENING_EXECUTION_LEDGER.md`

Commit:

- pending first branch commit

### Step 2 - Fix the non-Latin LaTeX emission defect

Status: pending

Targets:

- `src/fontshow/catalog/document.py`
- `tests/test_catalog_document.py`
- `tests/test_deterministic_output.py`

### Step 3 - Remove obsolete TeX-side bookkeeping from default output

Status: pending

Targets:

- `src/fontshow/latex/templates.py`
- `src/fontshow/catalog/document.py`
- `tests/test_catalog_document.py`
- `tests/test_artifact_hygiene.py`

Issue map:

- `#70`

### Step 4 - Add opt-in indexed navigation mode

Status: pending

Targets:

- `src/fontshow/cli/create_catalog.py`
- `src/fontshow/catalog/document.py`
- `src/fontshow/latex/templates.py`
- `tests/cli/test_create-catalog.py`
- `tests/test_catalog_document.py`

Issue map:

- `#70`

### Step 5 - Add selective archive controls

Status: pending

Targets:

- `src/fontshow/cli/create_catalog.py`
- `src/fontshow/catalog/pipeline.py`
- `tests/cli/test_create-catalog.py`
- `tests/test_create_catalog_runtime.py`

Issue map:

- `#59`

### Step 6 - Improve specimen usefulness without misrepresenting specialized fonts

Status: pending

Targets:

- `src/fontshow/catalog/document.py`
- `src/fontshow/inventory/specimens.py` if needed
- `src/fontshow/common/specimens.py` if needed
- `tests/test_catalog_document.py`
- `tests/test_inventory_specimens.py`

Issue map:

- no dedicated issue yet if this becomes first-class policy

### Step 7 - Compact visual layout pass

Status: pending

Targets:

- `src/fontshow/latex/templates.py`
- `src/fontshow/catalog/document.py`
- `tests/test_catalog_document.py`

### Step 8 - ADR decision checkpoint

Status: pending

Decision:

- pending

### Step 9 - Final validation and issue closure pass

Status: pending

Required validation:

```bash
pre-commit run --all-files
pytest -q
```
