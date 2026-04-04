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

- `72b78a8` - planning baseline committed

### Step 2 - Fix the non-Latin LaTeX emission defect

Status: completed

Targets:

- `src/fontshow/catalog/document.py`
- `tests/test_catalog_document.py`
- `tests/test_deterministic_output.py`

Verified work:

- fixed the language-wrapped render branch to emit `\\begingroup`
  literally instead of injecting ASCII backspace via `\b`
- added a regression assertion that the rendered block contains no
  backspace control character
- ran targeted regression test:
  `source .venv/bin/activate && pytest -q tests/test_catalog_document.py -k non_latin_template_when_language_is_available`

Commit:

- `6a3f64f` - non-Latin render defect fixed and regression-covered

### Step 3 - Remove obsolete TeX-side bookkeeping from default output

Status: completed

Targets:

- `src/fontshow/latex/templates.py`
- `src/fontshow/catalog/document.py`
- `tests/test_catalog_document.py`
- `tests/test_artifact_hygiene.py`

Issue map:

- `#70`

Verified work:

- removed unconditional TOC emission from the default LaTeX template
- removed legacy default-mode `\openout`, `\LogWorking`, `\LogBroken`,
  `\LogExcluded`, and `\FileSec` machinery
- stopped emitting obsolete `\Log*` calls from catalog document
  rendering
- reduced the default closing section to a minimal summary without
  working/broken/excluded end tables
- ran focused validation:
  - `source .venv/bin/activate && pytest -q tests/test_catalog_document.py`
  - `source .venv/bin/activate && pytest -q tests/test_artifact_hygiene.py`

Commit:

- `29b13a3` - default output no longer emits legacy TeX bookkeeping

### Step 4 - Add opt-in indexed navigation mode

Status: completed

Targets:

- `src/fontshow/cli/create_catalog.py`
- `src/fontshow/catalog/document.py`
- `src/fontshow/latex/templates.py`
- `tests/cli/test_create-catalog.py`
- `tests/test_catalog_document.py`

Issue map:

- `#70`

Verified work:

- added explicit `--indexed-navigation` CLI support and propagated it
  into catalog rendering metadata
- added deterministic family anchors in indexed mode
- enabled clickable TOC emission in indexed mode only
- added a Python-generated end-of-document navigation index linked to
  the rendered family anchors
- updated completion metadata and regenerated the checked-in bash
  completion script
- updated the stale template test that still required removed auxiliary
  logging macros
- ran focused validation:
  - `source .venv/bin/activate && pytest -q tests/test_catalog_document.py tests/test_create_catalog_runtime.py tests/cli/test_create-catalog.py`
  - `source .venv/bin/activate && pytest -q tests/test_bash_completion.py tests/test_latex_templates.py`

Commit:

- `7fac637` - indexed navigation mode committed and push blocker fixed

### Step 5 - Add selective archive controls

Status: completed

Targets:

- `src/fontshow/cli/create_catalog.py`
- `src/fontshow/catalog/pipeline.py`
- `tests/cli/test_create-catalog.py`
- `tests/test_create_catalog_runtime.py`
- `tests/test_catalog_pipeline.py`
- `tests/test_bash_completion.py`
- `scripts/completions/fontshow.bash`

Issue map:

- `#59`

Verified work:

- added repeatable `--language` selectors with deterministic
  normalization and OR-within-family matching
- added repeatable `--script` selectors with deterministic
  normalization and OR-within-family matching
- combined language and script selector families AND-wise in the
  catalog pipeline
- added repeatable `--sort-by language|script` ordering keys layered
  ahead of the default family ordering
- propagated the new selector and sort flags into generated catalog
  metadata and regenerated the checked-in bash completion script
- ran focused validation:
  - `source .venv/bin/activate && pytest -q tests/test_catalog_pipeline.py tests/test_create_catalog_runtime.py tests/cli/test_create-catalog.py tests/test_bash_completion.py`
  - `source .venv/bin/activate && ruff check src/fontshow/catalog/pipeline.py src/fontshow/cli/create_catalog.py tests/test_catalog_pipeline.py tests/test_create_catalog_runtime.py tests/cli/test_create-catalog.py tests/test_bash_completion.py`

Commit:

- `e49c719` - selective archive controls committed

### Step 6 - Improve specimen usefulness without misrepresenting specialized fonts

Status: completed

Targets:

- `src/fontshow/catalog/document.py`
- `src/fontshow/inventory/schema_accessors.py`
- `tests/test_catalog_document.py`
- `tests/test_inventory_specimens.py`
- `docs/decisions/0027-catalog-low-information-specimen-rendering-policy.md`
- `docs/decisions/index.md`

Issue map:

- no dedicated issue yet if this becomes first-class policy

ADR trigger:

- specialized-font specimen handling became an explicit renderer policy
  rather than incidental fallback behavior

Verified work:

- reused curated script specimens for low-information primary specimens
  when the font still behaves like a text font
- suppressed low-information specialized-font primary specimens instead
  of fabricating misleading text output
- added catalog tests covering both the curated replacement path and the
  specialized-font suppression path
- added Decision 0027 to record the renderer-local specimen policy
- ran focused validation:
  - `source .venv/bin/activate && pytest -q tests/test_catalog_document.py tests/test_inventory_specimens.py`
  - `source .venv/bin/activate && ruff check src/fontshow/catalog/document.py src/fontshow/inventory/schema_accessors.py tests/test_catalog_document.py tests/test_inventory_specimens.py`

Commit:

- `ca1bea7` - low-information specimen rendering hardened

### Step 7 - Compact visual layout pass

Status: completed

Targets:

- `src/fontshow/latex/templates.py`
- `src/fontshow/catalog/document.py`
- `tests/test_catalog_document.py`

Verified work:

- tightened the default compact-mode list spacing to reduce vertical
  waste in non-indexed catalogs
- reduced compact specimen rendering size without changing the extended
  metadata contract
- tightened title-page visual density with smaller frontmatter
  typography, smaller title scale, and narrower page margins
- updated compact-layout catalog tests to pin the denser spacing
- ran focused validation:
  - `source .venv/bin/activate && pytest -q tests/test_catalog_document.py tests/test_latex_templates.py`
  - `source .venv/bin/activate && ruff check src/fontshow/catalog/document.py src/fontshow/latex/templates.py tests/test_catalog_document.py tests/test_latex_templates.py`
  - `source .venv/bin/activate && mypy src/fontshow/catalog/document.py`

Commit:

- `3941b44` - compact catalog layout tightened

### Step 8 - ADR decision checkpoint

Status: completed

Decision:

- Decision 0027 created because specialized-font specimen handling is
  now an explicit catalog rendering policy

### Step 9 - Final validation and issue closure pass

Status: completed

Required validation:

```bash
pre-commit run --all-files
pytest -q
```

Validation result:

- `source .venv/bin/activate && pre-commit run --all-files`
- `source .venv/bin/activate && pytest -q`
- both commands passed on `2026-04-04`

### Step 10 - Schema 1.4 render-path loadability contract

Status: completed

Targets:

- `src/fontshow/schema/inventory_v1_4.json`
- `src/fontshow/core/global_constants.py`
- `src/fontshow/inventory/schema_accessors.py`
- `src/fontshow/inventory/font_descriptor.py`
- `src/fontshow/inventory/loadability.py`
- `src/fontshow/cli/parse_inventory.py`
- `src/fontshow/catalog/document.py`
- `tests/test_dump_loadability.py`
- `tests/test_inventory_loadability_helpers.py`
- `tests/test_catalog_document.py`
- `docs/decisions/0028-parse-inventory-render-path-loadability.md`

ADR trigger:

- persisted coarse loadability from `dump-fonts` no longer matched the
  stronger script-aware render paths emitted by the catalog renderer

Verified work:

- introduced schema `1.4` with `loadability.lualatex.render_variants`
  as the authoritative per-render-path validation record
- kept schema `1.3` intact as the historical contract and added the new
  schema resource and schema documentation alongside it
- changed `parse-inventory` to refresh current-install LuaLaTeX
  validation metadata and probe script-aware render variants after
  inference/specimen/render-policy enrichment
- persisted render-variant validation records through schema-aware
  accessors and updated the coarse top-level summary from the primary
  render path
- gated catalog specimen emission on persisted render-variant success so
  unvalidated secondary script blocks are no longer emitted by default
- added ADR 0028 to record the contract change from
  `dump-fonts`-only install touching to `dump-fonts` plus
  `parse-inventory`
- updated schema-aware tests, fixtures, inventory docs indices, and
  catalog regression coverage for the new contract

Required validation:

```bash
source .venv/bin/activate && pre-commit run --all-files
source .venv/bin/activate && pytest -q
```

Validation result:

- both commands passed on `2026-04-04`

### Step 11 - Parse-inventory CLI noise reduction

Status: completed

Targets:

- `src/fontshow/cli/parse_inventory.py`
- `src/fontshow/diagnostics/inventory_warnings.py`
- `tests/test_parse_inventory_runtime.py`
- `tests/test_inventory_warnings.py`
- `tests/cli/test_parse-inventory.py`
- `tests/test_bash_completion.py`
- `scripts/completions/fontshow.bash`

Verified work:

- changed verbose warning emission so `_emit_verbose_warnings()` is
  gated by the actual CLI verbose flag
- changed `--list-missing-language-coverage` to print a summary count by
  default instead of one line per matching font
- added `--show-all-missing-language-coverage` to restore the previous
  full listing behavior explicitly
- treated `--verbose` as an opt-in expansion path for the
  missing-language report
- updated completion expectations and regenerated the checked-in bash
  completion script

Required validation:

```bash
source .venv/bin/activate && pre-commit run --all-files
source .venv/bin/activate && pytest -q
```

Validation result:

- both commands passed on `2026-04-04`

Issue closure assessment:

- `#70` complete on this branch
- `#59` complete on this branch

Commit:

- pending final ledger commit with issue-closing footers
