# Assumptions Evaluation - 24/04/2026

## 0. Repository Snapshot

root:

- path: `C:/Users/marco/Documenti/Programmazione/Fontshow`
- git_head: `5cf123337a3a57cffaf91eb1dc24e46dc7ac7bab`
- git_status: clean at audit start
- adr_location: `docs/decisions/`
- configs: `pyproject.toml`, `.pre-commit-config.yaml`, `package.json`, `commitlint.config.cjs`, `.github/workflows/*.yml`
- entry_points: `pyproject.toml:50-51`, `src/fontshow/__main__.py:354-387`
- test_structure: `tests/`, `tests/cli/`, `tests/preflight/`, `tests/schema/`

## 1. ADR Summary

| ADR | title | status | evidence |
|---|---|---|---|
| 0001 | Base-Zero Replanning and Governance Reset | Accepted | `docs/decisions/0001-base-zero-replanning.md:1-3` |
| 0002 | Planning System Formalization | Accepted | `docs/decisions/0002-planning-system-formalization.md:1-3` |
| 0003 | Python and Node.js Coexistence Strategy | Accepted | `docs/decisions/0003-python-node-coexistence.md:1-5` |
| 0004 | Branching Strategy Formalization | Accepted | `docs/decisions/0004-branch-strategy.md:1-5` |
| 0005 | CLI error handling normalization | Accepted | `docs/decisions/0005-cli-error-handling-normalization.md:1-5` |
| 0006 | CLI dispatch testability limitation | Superseded | `docs/decisions/0006-cli-dispatch-testability-limit.md:1-6` |
| 0007 | Standardization of project scripts in Python | Accepted | `docs/decisions/0007-standardization-project-scripts-python.md:1-4` |
| 0008 | Developer tooling is first-class project code | Accepted | `docs/decisions/0008-developer-tooling-first-class-project-code.md:1-4` |
| 0009 | CLI verbosity contract | Accepted | `docs/decisions/0009-cli-verbosity-contract.md:1-4` |
| 0010 | Separation between CLI verbosity and debug-only inference output | Accepted | `docs/decisions/0010-separation-cli-verbosity-debug.md:1-4` |
| 0011 | CLI stdout / stderr semantics and quiet behavior | Accepted | `docs/decisions/0011-cli-stdout-stderr-semantics-quiet-behavior.md:1-6` |
| 0012 | GitHub Pages deployment strategy | Accepted | `docs/decisions/0012-github-pages-deployment-strategy.md:1-4` |
| 0013 | Language normalization strategy | Accepted | `docs/decisions/0013-language-normalization-strategy.md:1-4` |
| 0014 | Exclude bitmap / non-OpenType fonts from inventory | Accepted | `docs/decisions/0014-exclude-bitmap-non-opentype-fonts-inventory.md:1-4` |
| 0015 | ASCII-only console output | Accepted | `docs/decisions/0015-ascii-console-output.md:1-4` |
| 0016 | Language Normalization and Validation Strategy | Accepted | `docs/decisions/0016-language-normalization-validation-strategy.md:1-4` |
| 0017 | Ruff Linting Policy and Staged Adoption | Accepted | `docs/decisions/0017-ruff-linting-policy-staged-adoption.md:1-4` |
| 0018 | TRACE Logging Architecture and Semantics | Accepted | `docs/decisions/0018-trace-logging-architecture-semantics.md:1-4` |
| 0019 | Enum / JSON Boundary Invariant | Accepted | `docs/decisions/0019-enum-json-boundary-invariant.md:1-4` |
| 0020 | Schema v1.2 Unification and Deprecation | Accepted | `docs/decisions/0020-schema-v1-2-unification-deprecation-previous-versions.md:1-4` |
| 0021 | Authoritative Unicode Ontology | Accepted | `docs/decisions/0021-authoritative-unicode-ontology.md:1-4` |
| 0022 | Specimen Inference Inputs Matrix v1.0 | Accepted | `docs/decisions/0022-fontshow-specimen-inference-inputs-matrix-v1-0.md:1-4` |
| 0023 | Font skip accounting and legacy format filtering | Accepted | `docs/decisions/0023-font-skip-accounting-legacy-format-filtering.md:1-4` |
| 0024 | Parse-inventory validation summary and fallback handling | Accepted | `docs/decisions/0024-parse-inventory-validation-summary-fallback-handling.md:1-4` |
| 0025 | Drive Script Inference from Ontology Data | Accepted | `docs/decisions/0025-drive-script-inference-ontology-data.md:1-4` |
| 0026 | Schema v1.3 nested inventory structure | Accepted | `docs/decisions/0026-schema-v1-3-nested-inventory-structure-latex-validation-metadata.md:1-4` |
| 0027 | Catalog low-information specimen rendering policy | Accepted | `docs/decisions/0027-catalog-low-information-specimen-rendering-policy.md:1-4` |
| 0028 | Parse-Inventory Render-Path Loadability | Accepted | `docs/decisions/0028-parse-inventory-render-path-loadability.md:1-3` |
| 0029 | dump-fonts controlled discovery paths | Accepted | `docs/decisions/0029-dump-fonts-controlled-discovery-paths.md:1-3` |

## 2. Explicit Assumptions

ADR_0001:
  title: Base-Zero Replanning and Governance Reset
  status: Accepted
  decision: legacy planning archived; new planning framework under `docs/planning`
  assumptions: new work originates from `docs/planning`; future governance decisions use `docs/decisions`
  consequences: old milestones archived; new work tracked through new model
  evidence:
    - file: `docs/decisions/0001-base-zero-replanning.md`
      lines: `28-76`
      snippet: `New work MUST originate from docs/planning`

ADR_0003:
  title: Python and Node.js Coexistence Strategy
  status: Accepted
  decision: Python and Node tooling coexist in one workspace
  assumptions: Node tooling is development-only; Python package discovery must be restricted
  consequences: editable installs and CI builds remain stable
  evidence:
    - file: `docs/decisions/0003-python-node-coexistence.md`
      lines: `19-36`
      snippet: `Node.js tooling is considered development-only`

ADR_0005:
  title: CLI error handling normalization
  status: Accepted
  decision: exit codes `0`, `1`, `2` distinguish success, expected errors, internal errors
  assumptions: CLI callers depend on stable exit-code semantics
  consequences: internal failures detectable via exit code `2`
  evidence:
    - file: `docs/decisions/0005-cli-error-handling-normalization.md`
      lines: `36-99`
      snippet: `Exit code 2`

ADR_0009:
  title: CLI verbosity contract
  status: Accepted
  decision: define `--quiet`, default, and `--verbose`
  assumptions: automation relies on no stdout in quiet mode
  consequences: predictable CLI behavior
  evidence:
    - file: `docs/decisions/0009-cli-verbosity-contract.md`
      lines: `30-142`
      snippet: `Produces no stdout output`

ADR_0011:
  title: CLI stdout / stderr semantics and quiet behavior
  status: Accepted
  decision: `--quiet` suppresses stdout but not warnings/errors on stderr
  assumptions: stderr diagnostics remain valid under quiet mode
  consequences: tests align with real CLI behavior
  evidence:
    - file: `docs/decisions/0011-cli-stdout-stderr-semantics-quiet-behavior.md`
      lines: `54-119`
      snippet: `stderr is allowed output`

ADR_0014:
  title: Exclude bitmap / non-OpenType fonts from inventory
  status: Accepted
  decision: exclude non-OpenType / unparseable fonts during `dump-fonts`
  assumptions: later pipeline stages only process semantically parseable OpenType/TrueType fonts
  consequences: bitmap fonts skipped; no parse/schema changes
  evidence:
    - file: `docs/decisions/0014-exclude-bitmap-non-opentype-fonts-inventory.md`
      lines: `29-58`
      snippet: `never reach later pipeline stages`

ADR_0018:
  title: TRACE Logging Architecture and Semantics
  status: Accepted
  decision: TRACE has semantic categories, activation model, output rules, performance contract
  assumptions: TRACE is high-frequency and must be deterministic/filterable
  consequences: logging stability guarantees and guardrails
  evidence:
    - file: `docs/decisions/0018-trace-logging-architecture-semantics.md`
      lines: `24-247`
      snippet: `TRACE MUST be used for`

ADR_0021:
  title: Authoritative Unicode Ontology
  status: Accepted
  decision: generated Unicode ontology from vendored standards
  assumptions: Unicode behavior derives from vendored UCD and ISO data
  consequences: deterministic Unicode behavior; generator critical
  evidence:
    - file: `docs/decisions/0021-authoritative-unicode-ontology.md`
      lines: `27-86`
      snippet: `vendored standards`

ADR_0028:
  title: Parse-Inventory Render-Path Loadability
  status: Accepted
  decision: `parse-inventory` refreshes render-path loadability against current install
  assumptions: parse output may depend on LuaLaTeX/fontspec environment
  consequences: inventories may diverge across TeX installations
  evidence:
    - file: `docs/decisions/0028-parse-inventory-render-path-loadability.md`
      lines: `30-75`
      snippet: `parse-inventory is no longer a pure JSON-only enrichment step`

ADR_0029:
  title: dump-fonts controlled discovery paths
  status: Accepted
  decision: `dump-fonts --paths` scans only provided directories
  assumptions: invalid roots fail; no system fallback in paths mode
  consequences: reproducible benchmark inputs
  evidence:
    - file: `docs/decisions/0029-dump-fonts-controlled-discovery-paths.md`
      lines: `19-50`
      snippet: `platform system discovery is not used as a fallback`

## 3. Implicit Assumptions

environment:

ASSUMPTION_ENV_001:
  description: Python 3.13 is the project runtime/test/tooling baseline.
  category: environment
  evidence:
    - file: `pyproject.toml`
      lines: `10-17`
      snippet: `requires-python = ">=3.13"`
    - file: `.github/workflows/ci.yml`
      lines: `27-38`
      snippet: `python-version: "3.13"`
  confidence: high

ASSUMPTION_ENV_002:
  description: Linux bare-metal is the fully supported baseline; Windows is warning-level; macOS is unsupported/error-level.
  category: environment
  evidence:
    - file: `src/fontshow/preflight/checks/environment.py`
      lines: `127-129`
      snippet: `Linux bare-metal is treated as the fully supported baseline`
    - file: `tests/preflight/test_environment_matrix.py`
      lines: `34-42`
      snippet: `("macos", "bare-metal", Severity.ERROR)`
  confidence: high

ASSUMPTION_ENV_003:
  description: LuaLaTeX is required for catalog generation and checked through PATH plus deterministic Windows fallback paths.
  category: environment
  evidence:
    - file: `src/fontshow/preflight/checks/latex.py`
      lines: `4-10`
      snippet: `LuaLaTeX engine required for catalog generation`
    - file: `src/fontshow/preflight/checks/latex.py`
      lines: `395-424`
      snippet: `shutil.which("lualatex")`
  confidence: high

tooling:

ASSUMPTION_TOOL_001:
  description: Runtime Python distribution depends on `jsonschema`, `language-tags`, `pycountry`, and `fonttools`.
  category: tooling
  evidence:
    - file: `pyproject.toml`
      lines: `13-18`
      snippet: `"fonttools>=4.61.0"`
  confidence: high

ASSUMPTION_TOOL_002:
  description: Release automation depends on Node 20 and semantic-release.
  category: tooling
  evidence:
    - file: `.github/workflows/release.yml`
      lines: `29-60`
      snippet: `node-version: 20`
    - file: `package.json`
      lines: `25-33`
      snippet: `"semantic-release": "24.2.9"`
  confidence: high

ASSUMPTION_TOOL_003:
  description: CI quality gates are `pre-commit run --all-files` plus pytest with coverage.
  category: tooling
  evidence:
    - file: `.github/workflows/ci.yml`
      lines: `46-52`
      snippet: `pre-commit run --all-files`
  confidence: high

data:

ASSUMPTION_DATA_001:
  description: Current canonical inventory schema is v1.5.
  category: data
  evidence:
    - file: `src/fontshow/schema/inventory_v1_5.json`
      lines: `3-5`
      snippet: `Fontshow Inventory Schema v1.5`
    - file: `tests/test_output_schema_invariants.py`
      lines: `47-48`
      snippet: `"schema_version": "1.5"`
  confidence: high

ASSUMPTION_DATA_002:
  description: Valid inventory entries require persisted per-font LuaLaTeX loadability state including `render_variants`.
  category: data
  evidence:
    - file: `src/fontshow/schema/inventory_v1_5.json`
      lines: `393-408`
      snippet: `"required": ["lualatex"]`
    - file: `tests/test_output_schema_invariants.py`
      lines: `120-127`
      snippet: `"render_variants": []`
  confidence: high

ASSUMPTION_DATA_003:
  description: Unicode/ISO inference uses vendored Unicode 17.0.0 and ISO 15924 data.
  category: data
  evidence:
    - file: `src/fontshow/ontology/unicode_tables.py`
      lines: `1-8`
      snippet: `Unicode version: 17.0.0`
    - file: `src/fontshow/data/unicode/README.md`
      lines: `7-13`
      snippet: `vendored to guarantee`
  confidence: high

ASSUMPTION_DATA_004:
  description: Language inference ignores platform charset metadata and uses Unicode coverage data.
  category: data
  evidence:
    - file: `src/fontshow/inventory/infer_languages.py`
      lines: `15-18`
      snippet: `Platform-specific charset metadata is intentionally ignored`
    - file: `src/fontshow/inventory/infer_languages.py`
      lines: `43-45`
      snippet: `LANGUAGE_BLOCK_COVERAGE_THRESHOLD = 0.40`
  confidence: high

api:

ASSUMPTION_API_001:
  description: Public CLI commands are `preflight`, `dump-fonts`, `parse-inventory`, `validate-inventory`, and `create-catalog`.
  category: api
  evidence:
    - file: `src/fontshow/__main__.py`
      lines: `240-245`
      snippet: `fontshow dump-fonts`
    - file: `src/fontshow/__main__.py`
      lines: `262-273`
      snippet: `subparsers.add_parser("preflight")`
  confidence: high

ASSUMPTION_API_002:
  description: CLI handlers return integer-like exit codes or `None`; uncaught exceptions map to exit code `2`.
  category: api
  evidence:
    - file: `src/fontshow/__main__.py`
      lines: `296-307`
      snippet: `2 for any other unhandled exception`
    - file: `tests/test_main_dispatch.py`
      lines: `18-19`
      snippet: `map correctly`
  confidence: high

workflow:

ASSUMPTION_WORKFLOW_001:
  description: Documentation is built with MkDocs strict mode and deployed through GitHub Actions.
  category: workflow
  evidence:
    - file: `.github/workflows/docs-pages.yml`
      lines: `22-44`
      snippet: `mkdocs build --strict`
  confidence: high

ASSUMPTION_WORKFLOW_002:
  description: Tests intentionally ignore cache/temp directories during discovery.
  category: workflow
  evidence:
    - file: `pyproject.toml`
      lines: `53-64`
      snippet: `norecursedirs`
  confidence: high

performance:

ASSUMPTION_PERF_001:
  description: JSON formatting is deterministic and appends a trailing newline.
  category: performance
  evidence:
    - file: `src/fontshow/core/json_format.py`
      lines: `315-322`
      snippet: `deterministic layout and trailing newline`
    - file: `tests/test_deterministic_output.py`
      lines: `83-85`
      snippet: `byte-stable`
  confidence: high

ASSUMPTION_PERF_002:
  description: TRACE logging must be disabled/no-op by default and low overhead.
  category: performance
  evidence:
    - file: `src/fontshow/core/logging_utils.py`
      lines: `17-19`
      snippet: `no-ops with minimal overhead`
    - file: `src/fontshow/core/logging_utils.py`
      lines: `41-47`
      snippet: `Logging is disabled by default`
  confidence: high

## 4. Coverage Matrix

ASSUMPTION_ENV_001 -> NONE
  classification: NOT_COVERED
  justification: Python/Node coexistence is covered by ADR_0003, but Python 3.13 baseline is not documented in a numbered ADR.

ASSUMPTION_ENV_002 -> NONE
  classification: NOT_COVERED
  justification: Platform severity matrix is enforced by preflight code/tests, but no active ADR defines Linux/Windows/macOS support levels.

ASSUMPTION_ENV_003 -> ADR_0028
  classification: PARTIALLY_COVERED
  justification: ADR_0028 covers LuaLaTeX/fontspec environment dependence for parse-time loadability; Windows fallback probing is code/test-only.

ASSUMPTION_TOOL_001 -> ADR_0003
  classification: PARTIALLY_COVERED
  justification: ADR_0003 covers Python packaging boundaries, not concrete runtime dependencies.

ASSUMPTION_TOOL_002 -> ADR_0003
  classification: PARTIALLY_COVERED
  justification: ADR_0003 covers Node as development-only; Node 20 and semantic-release versions are config-only.

ASSUMPTION_TOOL_003 -> NONE
  classification: NOT_COVERED
  justification: CI gates are workflow config, not active ADR content.

ASSUMPTION_DATA_001 -> ADR_0026
  classification: PARTIALLY_COVERED
  justification: ADR_0026 declares v1.3 authoritative; current v1.5 is not covered by a matching numbered ADR.

ASSUMPTION_DATA_002 -> ADR_0028
  classification: PARTIALLY_COVERED
  justification: ADR_0028 covers `render_variants`; v1.5 schema requirement is not separately ADR-covered.

ASSUMPTION_DATA_003 -> ADR_0021
  classification: COVERED_BY_ADR
  justification: ADR_0021 explicitly adopts vendored generated Unicode ontology.

ASSUMPTION_DATA_004 -> ADR_0025
  classification: PARTIALLY_COVERED
  justification: ADR_0025 covers ontology-driven inference; charset-ignore rule is explicit in code but not directly in ADR_0025.

ASSUMPTION_API_001 -> ADR_0009
  classification: PARTIALLY_COVERED
  justification: ADR_0009 defines CLI verbosity behavior; command inventory is code/config-defined.

ASSUMPTION_API_002 -> ADR_0005
  classification: COVERED_BY_ADR
  justification: ADR_0005 defines exit code semantics.

ASSUMPTION_WORKFLOW_001 -> ADR_0012
  classification: COVERED_BY_ADR
  justification: ADR_0012 defines GitHub Actions documentation deployment.

ASSUMPTION_WORKFLOW_002 -> NONE
  classification: NOT_COVERED
  justification: pytest recursion exclusions are config-only.

ASSUMPTION_PERF_001 -> NONE
  classification: NOT_COVERED
  justification: deterministic output is tested and implemented but not covered by a dedicated active ADR beyond adjacent schema/logging decisions.

ASSUMPTION_PERF_002 -> ADR_0018
  classification: COVERED_BY_ADR
  justification: ADR_0018 defines TRACE performance and stability guarantees.

## 5. High-Risk Hidden Assumptions

ASSUMPTION_ENV_002:
  risk: HIGH
  rationale: platform support levels affect portability and preflight correctness.
  evidence:
    - file: `tests/preflight/test_environment_matrix.py`
      lines: `34-42`
      snippet: `("macos", "bare-metal", Severity.ERROR)`

ASSUMPTION_DATA_001:
  risk: HIGH
  rationale: current authoritative schema is v1.5, while latest explicit schema authority ADR evidence stops at v1.3.
  evidence:
    - file: `src/fontshow/schema/inventory_v1_5.json`
      lines: `3-5`
      snippet: `Fontshow Inventory Schema v1.5`

ASSUMPTION_DATA_002:
  risk: HIGH
  rationale: persisted loadability fields affect inventory compatibility and render correctness.
  evidence:
    - file: `src/fontshow/schema/inventory_v1_5.json`
      lines: `393-408`
      snippet: `"render_variants"`

## 6. Suggested ADR Candidates

- proposed ADR title: `ADR: Platform Support and Preflight Severity Matrix`
  rationale: codify Linux/Windows/macOS support levels currently enforced only by code/tests.
- proposed ADR title: `ADR: Inventory Schema v1.5 Authority and Compatibility Contract`
  rationale: align current schema authority with decision records and document compatibility impact.
- proposed ADR title: `ADR: Persisted LuaLaTeX Loadability v1.5 Schema Contract`
  rationale: document required `loadability.lualatex.render_variants` behavior as a stable inventory contract.
