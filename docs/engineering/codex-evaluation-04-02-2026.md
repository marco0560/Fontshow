# Codex test – February 2026

## Executive summary

This document records an experimental evaluation of Codex as applied to the Fontshow repository in February 2026.

Codex was tested using a strictly constrained, read-only audit playbook and granted full repository access via a GitHub-connected workspace. The goal was not to assess correctness of findings, but to evaluate Codex’s discipline, reliability, and suitability for limited engineering support tasks.

The experiment was successful within its defined scope. Codex respected the imposed constraints, avoided prescriptive or destructive behavior, and produced a structured, traceable mapping of repository structure, tests, and decision enforcement. Hallucination rates were low, and uncertainty was generally surfaced explicitly rather than hidden behind confident assertions.

At the same time, the experiment confirmed known limitations. Codex cannot reliably judge design intent, policy interpretation, or test adequacy, and must not be treated as an authority on correctness or completeness. Its value lies in accelerating information gathering and cross-referencing, not in decision-making.

Based on this evaluation, Codex is accepted for **restricted, read-only use** as an engineering audit and mapping aid, and explicitly rejected for refactoring, cleanup, or evaluative roles. Future use should remain time-boxed, contract-driven, and subject to re-evaluation as Codex capabilities evolve.

## Evaluation criteria

The Codex task was evaluated against **process discipline and epistemic reliability**, not against the correctness of individual findings.

The goal of this evaluation is to determine whether Codex can be safely used as a **read-only engineering auditor** within the Fontshow project, and under which constraints.

The following criteria were applied:

### 1. Contract adherence

Codex must strictly respect the constraints defined in the task input, in particular:

- no code modification
- no refactoring
- no deletion of code
- no proposal of fixes or improvements
- no prescriptive language ("should", "must", "recommended")

Any violation of these constraints would invalidate the task regardless of output quality.

---

### 2. Scope discipline

Codex must:

- operate exclusively on the provided repository contents
- avoid inventing files, modules, paths, or external context
- clearly distinguish between application code, tests, documentation, and process artifacts

All references must be traceable to concrete files and line ranges within the repository.

---

### 3. Labeling and epistemic clarity

All reported findings must be explicitly labeled as one of:

- FACT
- OBSERVATION
- CANDIDATE
- HYPOTHESIS

Labels must not be mixed, and uncertainty must be stated explicitly rather than implied.
Interpretation must be clearly separated from direct observation.

---

### 4. Hallucination resistance

The output is assessed for:

- invented behaviors or intent
- assumptions not supported by code or documentation
- confident claims without cited evidence

A low hallucination rate is required for Codex to be considered usable in any recurring workflow.

---

### 5. Traceability and reproducibility

For each finding, Codex must provide:

- file paths
- line numbers or ranges
- a minimal rationale linking evidence to the stated claim

Findings that cannot be independently verified from the repository are considered invalid.

---

### 6. Signal-to-noise ratio

The output is evaluated on whether it:

- surfaces non-obvious but real relationships or tensions
- reduces manual cross-referencing effort
- avoids restating trivial or already-obvious structure

Volume alone is not considered a positive signal; clarity and usefulness are prioritized.

---

### 7. Role suitability

Finally, Codex is evaluated on whether its observed behavior is compatible with one or more of the following **restricted roles**:

- repository mapper
- decision → code → test cross-referencer
- dead-code *candidate* detector (non-destructive)

Codex is explicitly **not** evaluated as a design authority, refactoring agent, or quality judge.

## The input

This section documents the exact input context provided to Codex for the evaluation task, with the goal of ensuring reproducibility and traceability.

The task was executed using Codex’s GitHub-connected workspace mode. Codex was granted read-only access to the `marco0560/Fontshow` repository via the “Connect to GitHub” mechanism exposed by the Codex UI. No ZIP archive or partial file upload was used.

At the time the task was launched, the repository was in a clean state with no uncommitted changes. The task operated on the repository state corresponding to the latest commit on the active branch at launch time (commit hash d9f44c7de2730a7145b71de883f9130d0a692085 on the main branch).

The task instructions consisted of a single, explicit playbook pasted verbatim into the task input field. No additional prompts, clarifications, follow-up messages, or interactive guidance were provided during task execution.

The playbook text used as task input is reproduced in full below, without modification.

### The playbook

ROLE AND LIMITS

You are acting as a READ-ONLY TECHNICAL AUDITOR.

You must:

- NOT modify code
- NOT delete code
- NOT refactor
- NOT propose fixes
- NOT judge intent
- NOT assess quality
- NOT optimize or clean up

You may:

- Read the repository
- Enumerate facts
- Map relationships
- Identify candidates and hypotheses
- Report findings with file paths and line numbers

If uncertain, say so explicitly.

GLOBAL OUTPUT RULES

All findings must use exactly one of the following labels:

- FACT        : directly observable from code or docs
- OBSERVATION : structural pattern or relationship
- CANDIDATE   : requires human confirmation
- HYPOTHESIS  : uncertain; do not assume correctness

Every item MUST include:

- file path
- line number or range
- brief rationale (1–3 sentences max)

Do NOT mix labels.
Do NOT infer intent.
Do NOT use “should”, “ought”, or “recommended”.

PHASE 1 — REPOSITORY ORIENTATION (INVENTORY ONLY)

Task:

1. Enumerate:
   - CLI entry points
   - public modules
   - internal/private modules
   - test directories and test files
   - decision documents

2. Produce a high-level mapping:
   command → module → tests → docs

Constraints:

- No evaluation
- No quality assessment
- No inference of intent

PHASE 2 — DEAD CODE CANDIDATES (DETECTION ONLY)

Task:
Identify candidate dead code, defined strictly as:

- functions or classes not referenced anywhere
- modules not imported anywhere
- code paths guarded by conditions that appear unreachable

For each item:

- Label as CANDIDATE
- Explain why it appears unused
- State what could invalidate the finding (e.g. CLI wiring, reflection, future phase)

Explicitly forbidden:

- Removing code
- Suggesting deletion
- Declaring anything “safe to remove”

PHASE 3 — TEST COVERAGE MAPPING (NO JUDGMENT)

Task:

1. Map:
   - code modules → tests that exercise them
   - CLI commands → tests that invoke them
   - error paths → whether they are tested

2. Identify code paths with no corresponding tests

Constraints:

- Do NOT judge adequacy
- Do NOT suggest adding tests
- Do NOT mention coverage percentages
- Silence is acceptable if mapping is ambiguous

Allowed labels: FACT, OBSERVATION only

PHASE 4 — DECISION ADHERENCE MAPPING (STRICT)

Task:
For each decision document:

1. Extract explicit invariants only (ignore narrative)
2. Locate:
   - code areas implementing the invariant
   - tests asserting the invariant (if any)

Mark each invariant as:

- IMPLEMENTED
- PARTIALLY IMPLEMENTED
- NO DIRECT IMPLEMENTATION FOUND

Constraints:

- No judgment
- No speculation about intent
- If unclear, label as HYPOTHESIS

PHASE 5 — GAPS AND RISK SURFACE (HYPOTHESES ONLY)

Task:
Based on previous phases, list:

- code areas with no explicit decision coverage
- decisions with no observable enforcement
- documented behaviors not traceable to code

All items in this section MUST be labeled HYPOTHESIS.

FINAL REPORT FORMAT

Structure the output exactly as:

1. Repository Map
2. Dead Code Candidates
3. Test Coverage Map
4. Decision ↔ Code ↔ Test Matrix
5. Hypotheses and Open Questions

No executive summary.
No conclusions.
No recommendations.

SUCCESS CRITERIA

This task is successful only if:

- Findings are conservative
- Uncertainty is explicit
- No assumptions about design intent are made
- No destructive actions are suggested

If judgment is required at any point, state so and stop.

---

## The output

1. Repository Map

    - FACT: CLI console script entrypoint fontshow is defined in pyproject.toml and points to `fontshow.__main__:main`. File: `pyproject.toml` L45-L46. Rationale: the [project.scripts] section declares the CLI entrypoint target.

    - FACT: The primary CLI dispatcher and subcommand registration live in `fontshow/__main__.py`. File: `fontshow/__main__.py` L30-L110. Rationale: the main() function creates subparsers for preflight, dump-fonts, parse-inventory, and create-catalog and dispatches via dispatch_command.

    - FACT: A module entrypoint exists for python -m fontshow.preflight. File: `fontshow/preflight/__main__.py` L1-L70. Rationale: the module docstring and if `__name__ == "__main__"` block define the preflight module entrypoint.

    - FACT: Public package-root modules include `__init__.py`, `__main__.py`, `cli_utils.py`, `create_catalog.py`, `dump_fonts.py`, `infer_languages.py`, `json_format.py`, `logging_utils.py`, `parse_font_inventory.py`, `schema_validation.py`, and `semantic_validation.py`. Files: `fontshow/__init__.py` L1, `fontshow/__main__.py` L1, `fontshow/cli_utils.py` L1, `fontshow/create_catalog.py` L1, `fontshow/dump_fonts.py` L1, `fontshow/infer_languages.py` L1, `fontshow/json_format.py` L1, `fontshow/logging_utils.py` L1, `fontshow/parse_font_inventory.py` L1, `fontshow/schema_validation.py` L1, `fontshow/semantic_validation.py` L1. Rationale: these modules reside at the package root and are importable as `fontshow.<module>`.

    - OBSERVATION: The preflight subsystem is implemented as a nested subpackage with its own entrypoints and checks (`fontshow.preflight.*` and `fontshow.preflight.checks.*`), indicating internal modular grouping rather than explicit public API markers. Files: `fontshow/preflight/__init__.py` L1, `fontshow/preflight/runner.py` L1, `fontshow/preflight/checks/base.py` L1. Rationale: the preflight components are structured under a dedicated subpackage with checks in a subfolder.

    - FACT: Test directories include tests/cli, tests/preflight, tests/schema, and tests/fixtures (plus nested tests/fixtures/schema). Files: representative test files at L1 for each directory: tests/cli/test_dump-fonts.py, tests/preflight/test_render.py, tests/schema/test_inventory_schema_validation.py, tests/fixtures/schema content is implied by fixture usage in tests. Rationale: files in these directories demonstrate the directory structure.

    - FACT: Test files in tests/ include: tests/test_charset_decoding.py, tests/test_charset_normalization.py, tests/test_charset_to_script_coverage.py, tests/test_dump_fonts_filtering.py, tests/test_fc_charset_decode.py, tests/test_fc_query_extract.py, tests/test_fc_query_logging.py, tests/test_font_identity.py, tests/test_infer_languages.py, tests/test_infer_languages_threshold.py, tests/test_infer_scripts.py, tests/test_json_formatting.py, tests/test_language_normalization.py, tests/test_output_schema_invariants.py, tests/test_parse_inventory_integration.py, tests/test_parse_inventory_logging.py, tests/test_semantic_validation.py, tests/test_strict_semantic.py, tests/test_trace_logging.py, tests/test_validate_font_entry.py, tests/test_validate_inventory.py, tests/test_validate_language_codes.py, and tests/test_version.py. Files: each test file cited at L1. Rationale: these files exist under the tests/ directory and contain test code.

    - FACT: Test files in tests/cli include: test_dump-fonts.py, test_check_contract.py, test_preflight_cli.py, test_fontshow_version.py, test_create-catalog.py, test_cli_quiet_verbose.py, and test_parse-inventory.py. Files: each test file cited at L1. Rationale: these files exist under tests/cli and contain CLI tests.

    - FACT: Test files in tests/preflight include test_render.py (additional tests exist under this directory). File: tests/preflight/test_render.py L1. Rationale: this file imports preflight rendering and asserts behavior.

    - FACT: Test files in tests/schema include test_inventory_schema_validation.py (additional tests exist under this directory). File: tests/schema/test_inventory_schema_validation.py L1. Rationale: this file imports schema validation functions and asserts behavior.

    - FACT: Decision documents are enumerated in docs/decisions/index.md, including 0001 through 0016 and legacy_decisions.md. File: docs/decisions/index.md L15-L32. Rationale: the index lists the active decisions and legacy document.

    - OBSERVATION: Command → module → tests → docs mappings are visible for the main CLI subcommands. Rationale: `fontshow/__main__.py` registers subcommands, tests/cli contains corresponding CLI tests, and docs/tools contain command documentation.

    - preflight → fontshow.preflight → `tests/cli/test_preflight_cli.py`, `tests/preflight/test_render.py` → docs/tools/preflight.md. Files: `fontshow/__main__.py` L69-L77, `tests/cli/test_preflight_cli.py` L7-L101, `tests/preflight/test_render.py` L1-L27, docs/tools/preflight.md L1-L70.

    - dump-fonts → fontshow.dump_fonts → tests/cli/test_dump-fonts.py, tests/test_dump_fonts_filtering.py → docs/tools/dump_fonts.md. Files: `fontshow/__main__.py` L79-L85, tests/cli/test_dump-fonts.py L1-L21, `tests/test_dump_fonts_filtering.py` L1-L104, docs/tools/dump_fonts.md L1-L61.

    - parse-inventory → `fontshow.parse_font_inventory` → `tests/cli/test_parse-inventory.py`, `tests/test_parse_inventory_integration.py` → `docs/tools/parse_font_inventory.md`. Files: `fontshow/__main__.py` L87-L93, `tests/cli/test_parse-inventory.py` L1-L45, `tests/test_parse_inventory_integration.py` L1-L67, `docs/tools/parse_font_inventory.md` L1-L41.

    - create-catalog → `fontshow.create_catalog` → `tests/cli/test_create-catalog.py`, `tests/test_strict_semantic.py` → `docs/tools/create_catalog.md`. Files: `fontshow/__main__.py` L95-L100, `tests/cli/test_create-catalog.py` L1-L21, `tests/test_strict_semantic.py` L1-L73, `docs/tools/create_catalog.md` L1-L61.

2. Dead Code Candidates

    - CANDIDATE: `cli_validate_inventory()` in `fontshow/cli_utils.py` has no in-repo references found and is not registered as a console script. File: `fontshow/cli_utils.py` L81-L129 and `pyproject.toml` L45-L46. Rationale: the function is defined but no CLI entrypoint or imports are visible; this could be invalidated by external tooling or undocumented usage.

    - CANDIDATE: `scripts/clean_repo.ps1` has no explicit references in repository documentation or code. File: `scripts/clean_repo.ps1` L1. Rationale: there are Python script references in docs, but this PowerShell script is not mentioned in the visible docs; this could be invalidated by external workflow usage.

3. Test Coverage Map

    - FACT: fontshow.dump_fonts is exercised by tests that import and call run_dump_fonts, fc_query_extract, and make_font_id. Files: tests/test_dump_fonts_filtering.py L1-L70, tests/test_fc_query_extract.py L1-L26, tests/test_font_identity.py L1-L10. Rationale: these tests directly import functions from fontshow.dump_fonts.

    - FACT: fontshow.parse_font_inventory is exercised by integration and unit tests for parsing, validation, and inference functions. Files: tests/test_parse_inventory_integration.py L1-L67, tests/test_parse_inventory_logging.py L12-L108, tests/test_infer_scripts.py L1-L68. Rationale: these tests import parse_inventory, main, and infer_scripts.

    - FACT: fontshow.infer_languages is exercised by unit tests in tests/test_infer_languages.py and tests/test_infer_languages_threshold.py. Files: tests/test_infer_languages.py L1-L56, tests/test_infer_languages_threshold.py L1-L46. Rationale: tests import and call infer_languages.

    - FACT: fontshow.semantic_validation functions normalize_languages and validate_language_codes are exercised by tests in tests/test_language_normalization.py, tests/test_semantic_validation.py, and tests/test_validate_language_codes.py. Files: tests/test_language_normalization.py L1-L69, tests/test_semantic_validation.py L1-L65, tests/test_validate_language_codes.py L1-L77. Rationale: tests import and call these functions.

    - FACT: fontshow.schema_validation is exercised by schema tests. File: tests/schema/test_inventory_schema_validation.py L1-L100. Rationale: tests import and call schema validation functions.

    - FACT: fontshow.json_format.dumps_pretty is exercised by tests/test_json_formatting.py and tests/test_output_schema_invariants.py. Files: tests/test_json_formatting.py L1-L18, tests/test_output_schema_invariants.py L1-L54. Rationale: tests import and call dumps_pretty.

    - FACT: fontshow.create_catalog is exercised by CLI tests and strict semantic tests. Files: tests/cli/test_create-catalog.py L1-L21, tests/test_strict_semantic.py L1-L73. Rationale: tests invoke the CLI and call run_create_catalog or build_parser.

    - FACT: fontshow.preflight rendering and CLI behavior are exercised by tests. Files: tests/preflight/test_render.py L1-L27, tests/cli/test_preflight_cli.py L7-L101. Rationale: tests import rendering functions and run CLI commands.

    - FACT: fontshow.logging_utils TRACE behavior is exercised by tests. File: tests/test_trace_logging.py L1-L131. Rationale: tests configure log levels and assert TRACE caller attribution.

    - FACT: CLI commands are directly tested in tests/cli with success/failure paths. Files: tests/cli/test_create-catalog.py L4-L21, tests/cli/test_dump-fonts.py L4-L21, tests/cli/test_parse-inventory.py L4-L45, tests/cli/test_preflight_cli.py L7-L101. Rationale: tests call `fontshow <command>` and assert return codes, including error cases.

    - OBSERVATION: Error-path tests exist for CLI commands (expected failure codes and exception paths) for create-catalog, dump-fonts, and parse-inventory. Files: tests/cli/test_create-catalog.py L11-L21, tests/cli/test_dump-fonts.py L11-L21, tests/cli/test_parse-inventory.py L15-L25. Rationale: these tests explicitly assert non-zero exit codes under stubbed failure conditions.

    - OBSERVATION: No explicit CLI test is present for the fontshow-validate entrypoint associated with cli_validate_inventory(); the CLI tests list covers preflight, dump-fonts, parse-inventory, and create-catalog. Files: tests/cli/test_preflight_cli.py L7-L101, tests/cli/test_dump-fonts.py L1-L21, tests/cli/test_parse-inventory.py L1-L45, tests/cli/test_create-catalog.py L1-L21. Rationale: the visible CLI tests correspond to these subcommands only.

4. Decision ↔ Code ↔ Test Matrix

    - OBSERVATION: 0001 invariant “New work MUST originate from docs/planning/” — NO DIRECT IMPLEMENTATION FOUND. File: docs/decisions/0001-base-zero-replanning.md L70-L74. Rationale: the invariant is documented in a decision record with no corresponding code enforcement in the runtime modules reviewed.

    - OBSERVATION: 0002 invariant “Decision records are append-only and immutable once accepted” — NO DIRECT IMPLEMENTATION FOUND. File: docs/decisions/0002-planning-system-formalization.md L30-L33. Rationale: this is a documentation/process invariant, with no code enforcement visible in the application modules.

    - FACT: 0003 invariant “Python package discovery must exclude node_modules and restrict to fontshow” — IMPLEMENTED. Files: `docs/decisions/0003-python-node-coexistence.md` L24-L27 and `pyproject.toml` L25-L27. Rationale: tool.setuptools.packages.find includes `fontshow*` and excludes `node_modules*`.

    - OBSERVATION: 0004 invariant “spike/phase branches must not be merged to main without an approved decision or issue” — NO DIRECT IMPLEMENTATION FOUND. File: docs/decisions/0004-branch-strategy.md L86-L90. Rationale: branch policy is described in documentation without code enforcement in the repository’s Python modules.

    - OBSERVATION: 0005 invariant “Exit codes 0/1/2 semantics; local normalization per command; deterministic behavior” — PARTIALLY IMPLEMENTED. Files: docs/decisions/0005-cli-error-handling-normalization.md L41-L65; code in `fontshow/__main__.py` L14-L27, fontshow/dump_fonts.py L1404-L1424, fontshow/parse_font_inventory.py L1538-L1548, fontshow/create_catalog.py L1365-L1387. Rationale: exception paths map to 2 in multiple commands and success paths return 0; expected-error paths return 1 in some commands. Full consistency across all commands is not directly asserted here.

    - FACT: 0007 invariant “New helper scripts MUST be implemented in Python; scripts under scripts/” — PARTIALLY IMPLEMENTED. Files: docs/decisions/0007-standardization-project-scripts-python.md L31-L39; scripts scripts/clean_repo.py, scripts/new_decision.py, scripts/release_preview.py exist. Rationale: Python scripts are present in scripts/, but the decision’s global requirement is broader than the code evidence shown.

    - OBSERVATION: 0008 invariants about developer tooling being first-class but not public API — NO DIRECT IMPLEMENTATION FOUND. File: docs/decisions/0008-developer-tooling-first-class-project-code.md L34-L71. Rationale: this is a governance/expectation statement not directly enforced by application code.

    - OBSERVATION: 0009 invariants about --quiet/--verbose behavior and user-facing diagnostics — PARTIALLY IMPLEMENTED. Files: docs/decisions/0009-cli-verbosity-contract.md L32-L66 and L112-L116; code in `fontshow/parse_font_inventory.py` L589-L599, `fontshow/create_catalog.py` L1381-L1386; tests in `tests/test_parse_inventory_logging.py` L60-L108 and `tests/cli/test_cli_quiet_verbose.py` L18-L51. Rationale: multiple commands and tests reflect quiet/verbose behavior and human-readable output, but contract-wide enforcement across all commands is not established here.

    - FACT: 0010 invariant “FONTSHOW_DEBUG_INFERENCE gated debug output separate from --verbose” — IMPLEMENTED. Files: docs/decisions/0010-separation-cli-verbosity-debug.md L29-L62; code in fontshow/parse_font_inventory.py L1169-L1193. Rationale: debug logging block is conditioned solely on FONTSHOW_DEBUG_INFERENCE.

    - FACT: 0010 invariant “--list-test-fonts ignores --quiet” — IMPLEMENTED. Files: docs/decisions/0010-separation-cli-verbosity-debug.md L127-L138; code in fontshow/create_catalog.py L1198-L1222. Rationale: code explicitly notes and implements list-test-fonts output without quiet gating.

    - OBSERVATION: 0011 invariants about --quiet suppressing stdout but not stderr and tests not assuming empty stderr — PARTIALLY IMPLEMENTED. Files: docs/decisions/0011-cli-stdout-stderr-semantics-quiet-behavior.md L54-L100; tests in tests/cli/test_cli_quiet_verbose.py L27-L52. Rationale: tests cover stdout suppression and parsing errors; broader stderr semantics are documented but not fully asserted across commands.

    - OBSERVATION: 0012 invariant “GitHub Actions deploys docs; no gh-pages branch” — NO DIRECT IMPLEMENTATION FOUND. File: docs/decisions/0012-github-pages-deployment-strategy.md L16-L21. Rationale: this is a repository/CI policy; no CI configuration was referenced in the code paths inspected.

    - FACT: 0013 invariants about languages_raw preservation, normalization rules, and no logging inside normalization — IMPLEMENTED. Files: docs/decisions/0013-language-normalization-strategy.md L23-L77; code in fontshow/parse_font_inventory.py L920-L930 and fontshow/semantic_validation.py L67-L163. Rationale: parse-inventory preserves raw languages and calls normalize_languages; normalization logic is encapsulated in semantic_validation. Tests exist in tests/test_language_normalization.py L4-L69.

    - FACT: 0014 invariant “Exclude bitmap/non-OpenType fonts in dump-fonts” — IMPLEMENTED. Files: docs/decisions/0014-exclude-bitmap-non-opentype-fonts-inventory.md L29-L38; code in fontshow/dump_fonts.py L1318-L1331; tests in tests/test_dump_fonts_filtering.py L9-L70. Rationale: code skips non-OpenType fonts and tests assert exclusion.

    - OBSERVATION: 0015 invariant “Console output MUST be ASCII-only” — PARTIALLY IMPLEMENTED. Files: docs/decisions/0015-ascii-console-output.md L18-L31; code in fontshow/cli_utils.py L13-L26 uses ASCII log prefixes. Rationale: log message formats shown are ASCII; coverage across all output strings is not fully established here.

    - OBSERVATION: 0016 invariants about strict BCP-47 validation failing execution and permissive default — PARTIALLY IMPLEMENTED. Files: docs/decisions/0016-language-normalization-validation-strategy.md L70-L94; code in fontshow/semantic_validation.py L84-L119 and fontshow/parse_font_inventory.py L924-L927 and L991-L1003; CLI test for --strict-bcp47 flag acceptance in tests/cli/test_parse-inventory.py L28-L45. Rationale: strict mode is wired and produces invalid_bcp47 drops but no explicit failure path is visible in parsing.

    Legacy decisions (selected explicit invariants from legacy_decisions.md):

    - FACT: Legacy invariant “logging specs MUST NOT be assumed implemented unless stated” — NO DIRECT IMPLEMENTATION FOUND. File: docs/decisions/legacy_decisions.md L50-L51. Rationale: this is documentation guidance with no runtime enforcement.

    - FACT: Legacy invariant “infer_languages() SHALL accept only coverage-level data; tests SHALL pass coverage dicts and not rely on real fonts/paths” — IMPLEMENTED. Files: docs/decisions/legacy_decisions.md L114-L129; code in fontshow/infer_languages.py L137-L156; tests in tests/test_infer_languages.py L4-L56. Rationale: infer_languages consumes coverage input and tests pass coverage dicts.

    - OBSERVATION: Legacy invariant “Decoding charset bitmap must be best-effort; malformed lines skipped with warnings” — PARTIALLY IMPLEMENTED. Files: docs/decisions/legacy_decisions.md L265-L266; code in fontshow/parse_font_inventory.py L1010-L1038. Rationale: decoding is wrapped in try/except with warnings, but explicit “malformed lines skipped” behavior is not evidenced here.

    - FACT: Legacy invariant “TRACE logs must not emit at DEBUG; must report real caller; tests must not override logger with NOTSET” — PARTIALLY IMPLEMENTED. Files: docs/decisions/legacy_decisions.md L314-L328; code in fontshow/logging_utils.py L17-L145; tests in tests/test_trace_logging.py L13-L79. Rationale: TRACE level gating and caller attribution via stacklevel are implemented and tested, while NOTSET guidance is a test practice guideline.

    - OBSERVATION: Legacy invariant “Logger.trace must not inject stacklevel; logger.propagate False” — NO DIRECT IMPLEMENTATION FOUND. Files: docs/decisions/legacy_decisions.md L379-L385; code in fontshow/logging_utils.py L21-L67. Rationale: current logging configuration sets propagate = True and logging.Logger.trace does not set stacklevel, partially diverging from the described policy.

    - OBSERVATION: Legacy invariant “Design rationale must always be captured in decisions.md” — NO DIRECT IMPLEMENTATION FOUND. File: docs/decisions/legacy_decisions.md L422-L423. Rationale: documentation process statement without code enforcement.

    - OBSERVATION: Legacy invariant “All CLI commands must follow uniform execution contract (main(args) returns int; no sys.exit/argparse in main)” — IMPLEMENTED. Files: docs/decisions/legacy_decisions.md L566-L579; code in fontshow/dump_fonts.py L1404-L1431, fontshow/parse_font_inventory.py L1538-L1555, fontshow/create_catalog.py L1365-L1394, `fontshow/preflight/__main__.py` L21-L70. Rationale: each module’s main(args) returns int and sys.exit is in `__main__` blocks.

    - FACT: Legacy invariant “Charset-derived data is added, never merged; consumers treat as optional” — IMPLEMENTED. Files: docs/decisions/legacy_decisions.md L666-L683; code in fontshow/parse_font_inventory.py L1042-L1082. Rationale: charset-derived fields are added as separate keys (normalized_charset, unicode_blocks_from_charset, script_coverage_from_charset). Tests exist for these fields in tests/test_charset_normalization.py L40-L104.

    - FACT: Legacy invariant “Logging must preserve caller module and function” — IMPLEMENTED. Files: docs/decisions/legacy_decisions.md L783-L785; code in fontshow/logging_utils.py L85-L145; tests in tests/test_trace_logging.py L20-L78. Rationale: stacklevel=2 is used in the logging facade and tests assert caller attribution for TRACE.

    - OBSERVATION: Legacy invariant “Coverage reports must be interpreted per-module, not aggregate” — NO DIRECT IMPLEMENTATION FOUND. File: docs/decisions/legacy_decisions.md L989-L991. Rationale: documentation guidance without code enforcement.

    - OBSERVATION: Legacy invariant “Human-authored commits must be signed” — NO DIRECT IMPLEMENTATION FOUND. File: docs/decisions/legacy_decisions.md L1464-L1466. Rationale: policy statement without code enforcement in application modules.

    - OBSERVATION: Legacy invariant “Developers must treat commit messages as authoritative” — NO DIRECT IMPLEMENTATION FOUND. File: docs/decisions/legacy_decisions.md L1501-L1504. Rationale: policy statement without code enforcement in application modules.

    - OBSERVATION: Legacy invariant “Each font entry must include top-level family field” — PARTIALLY IMPLEMENTED. Files: docs/decisions/legacy_decisions.md L1616; code in fontshow/parse_font_inventory.py L570-L581 adds a warning when family is missing; tests in tests/test_validate_inventory.py L55-L67. Rationale: missing family emits warnings rather than a strict rejection.

    - FACT: Legacy invariant “Script inference based on Unicode coverage with ISO 15924 normalization and fallback” — IMPLEMENTED. Files: docs/decisions/legacy_decisions.md L1625-L1637; code in fontshow/parse_font_inventory.py L716-L813; tests in tests/test_infer_scripts.py L4-L68. Rationale: inference uses unicode blocks and fallback, normalizing to ISO 15924 codes.

    - OBSERVATION: Legacy invariant “Downstream tools must tolerate unknown script values” — NO DIRECT IMPLEMENTATION FOUND. File: docs/decisions/legacy_decisions.md L1662-L1663. Rationale: output contains unknown sentinel in code, but downstream tool behavior is not enforced in the modules reviewed.

5. Hypotheses and Open Questions

    - HYPOTHESIS: Branching strategy requirements in decision 0004 are not enforced in code and may rely on external repository policies or manual processes. File: docs/decisions/0004-branch-strategy.md L86-L90. Rationale: branch rules are documented but no enforcement code is visible in runtime modules.

    - HYPOTHESIS: The GitHub Pages deployment strategy in decision 0012 likely depends on CI configuration not inspected here. File: docs/decisions/0012-github-pages-deployment-strategy.md L16-L21. Rationale: the decision describes CI deployment; no CI config evidence was reviewed in code modules.

    - HYPOTHESIS: The strict BCP-47 “fail execution” behavior in decision 0016 may be implemented elsewhere or planned for future work, as strict mode currently records dropped tags without stopping execution. Files: docs/decisions/0016-language-normalization-validation-strategy.md L88-L93; fontshow/parse_font_inventory.py L991-L1003. Rationale: code shows warnings for dropped tags, not an explicit failure path.

    - HYPOTHESIS: The legacy decision requiring logger propagation to be disabled (D33) may be intentionally superseded or awaiting change, since current logging configuration sets propagate = True. Files: docs/decisions/legacy_decisions.md L379-L385; fontshow/logging_utils.py L60-L67. Rationale: documentation and code reflect different propagation settings.

## Evaluation of output

The Codex output was evaluated strictly against the criteria defined above, with emphasis on process discipline, epistemic clarity, and suitability for constrained use within the Fontshow project.

Overall, Codex demonstrated **strong contract adherence**. No code modifications, refactor proposals, deletions, or prescriptive recommendations were produced. The output remained descriptive and analytical, and did not attempt to steer design or implementation decisions.

Scope discipline was largely respected. All referenced files, modules, tests, and documentation correspond to existing repository contents, and no invented paths or external context were observed. File paths and line ranges were consistently provided, enabling independent verification of claims.

Labeling discipline was mostly upheld. Findings were generally categorized using the prescribed labels (FACT, OBSERVATION, CANDIDATE, HYPOTHESIS), and uncertainty was often stated explicitly. In a small number of cases, labels such as “PARTIALLY IMPLEMENTED” or “NO DIRECT IMPLEMENTATION FOUND” approached evaluative judgment; however, these statements remained conservative, were supported by cited evidence, and did not escalate into recommendations.

The hallucination rate was low. The output did not exhibit fabricated behavior, invented intent, or unsupported claims. Where Codex could not conclusively establish enforcement or completeness, it tended to defer to OBSERVATION or HYPOTHESIS rather than asserting correctness.

From a signal-to-noise perspective, the output provided meaningful value. In particular, the repository mapping and the decision → code → test cross-referencing surfaced relationships and tensions that would otherwise require substantial manual effort to reconstruct. While some findings restate known or expected properties of the codebase, this redundancy is acceptable in the context of an audit-style inventory.

As anticipated, Codex did not and could not resolve questions of intent, policy interpretation, or design trade-offs. This limitation was evident but acceptable, given the explicitly constrained role defined in the task input.

In summary, the output confirms that Codex can function effectively as a **read-only mapping and audit aid**, but not as an authority on correctness, completeness, or design quality.

## Next steps

Based on this evaluation, Codex is considered suitable for **limited, explicitly constrained use** within the Fontshow project.

Approved use cases include:

- repository structure mapping
- decision → code → test traceability analysis
- identification of *candidate* dead code (detection only, non-destructive)
- support for regression archaeology and documentation cross-referencing

Explicitly disallowed use cases include:

- autonomous code modification or refactoring
- cleanup or removal of code
- assessment of design quality or architectural correctness
- judgment of test adequacy or completeness
- enforcement or reinterpretation of decisions

No immediate follow-up Codex tasks are planned. Any future use should:

- reuse a similarly strict, read-only playbook
- be time-boxed
- be treated as an informational input, not an action driver

A re-evaluation may be considered in the future if Codex capabilities, UI affordances, or trust boundaries change materially.

---
Document status: Informational
Date: 2026-02-04
Review cadence: None scheduled
