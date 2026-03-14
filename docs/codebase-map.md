# Codebase Map

## Purpose

This document is a developer-oriented map of the Fontshow codebase.

It explains:

- the repository structure;
- the runtime pipeline;
- how a single font entry moves through the system;
- where to start when changing a subsystem;
- which areas are safe or risky to modify;
- where to look first when triaging a bug.

It is intended as a companion to:

- `docs/architecture.md`
- `docs/pipeline.md`
- the command-specific docs under `docs/tools/`

---

## High-level overview

Fontshow is a CLI pipeline for:

1. checking the environment;
2. discovering installed fonts;
3. serializing a raw inventory;
4. enriching and validating that inventory;
5. rendering a LaTeX catalog from the enriched data.

The main entrypoint is `fontshow/__main__.py`.

The top-level commands are:

- `preflight`
- `dump-fonts`
- `parse-inventory`
- `validate-inventory`
- `create-catalog`

The intended execution flow is:

```text
preflight
   ↓
dump-fonts
   ↓
parse-inventory
   ↓
validate-inventory   (optional as a separate explicit step)
   ↓
create-catalog
   ↓
LaTeX compilation outside the Python pipeline
```

---

## Package boundaries

### `fontshow/cli/`

Command orchestration only.

This layer:

- parses CLI arguments;
- coordinates workflow steps;
- returns exit codes;
- delegates real work to subsystem modules.

Important files:

- `fontshow/__main__.py`
- `fontshow/cli/dump_fonts.py`
- `fontshow/cli/parse_inventory.py`
- `fontshow/cli/validate_inventory.py`
- `fontshow/cli/create_catalog.py`

### `fontshow/inventory/`

Inventory model, enrichment, and validation.

This layer handles:

- raw font descriptor construction;
- charset normalization;
- Unicode block derivation;
- script inference;
- language inference;
- semantic validation;
- warning attachment;
- specimen generation.

Important files:

- `fontshow/inventory/font_descriptor.py`
- `fontshow/inventory/metadata_processing.py`
- `fontshow/inventory/infer_languages.py`
- `fontshow/inventory/script_analysis.py`
- `fontshow/inventory/semantic_validation.py`
- `fontshow/inventory/validation.py`
- `fontshow/inventory/schema_validation.py`

### `fontshow/catalog/`

Catalog-specific transformation from inventory records to renderable entries.

This layer handles:

- grouping and filtering;
- sample selection for catalog display;
- document assembly;
- label rendering.

Important files:

- `fontshow/catalog/pipeline.py`
- `fontshow/catalog/document.py`
- `fontshow/catalog/labels.py`

### `fontshow/latex/`

Low-level LaTeX rendering support.

This layer handles:

- escaping;
- script-aware render policy;
- templates;
- fontspec / Polyglossia decisions.

Important files:

- `fontshow/latex/render.py`
- `fontshow/latex/policy.py`
- `fontshow/latex/templates.py`

### `fontshow/platform/`

OS- and tool-specific integration.

This layer handles:

- installed font discovery;
- Fontconfig querying;
- runtime platform comparison.

Important files:

- `fontshow/platform/font_discovery.py`
- `fontshow/platform/fontconfig.py`
- `fontshow/platform/runtime.py`

### `fontshow/preflight/`

Environment validation subsystem.

This layer handles:

- environment support checks;
- capability checks;
- result aggregation;
- preflight CLI rendering.

Important files:

- `fontshow/preflight/runner.py`
- `fontshow/preflight/model.py`
- `fontshow/preflight/render.py`
- `fontshow/preflight/checks/*`

### `fontshow/core/`

Shared infrastructure.

This layer handles:

- CLI helpers;
- logging facade;
- JSON formatting;
- enum serialization boundary;
- warning structures;
- shared types and constants.

Important files:

- `fontshow/core/cli_utils.py`
- `fontshow/core/logging_utils.py`
- `fontshow/core/json_boundary.py`
- `fontshow/core/json_format.py`
- `fontshow/core/warnings.py`
- `fontshow/core/types.py`

### `fontshow/ontology/` and `fontshow/unicode/`

Static domain knowledge.

This layer provides:

- Unicode block/script tables;
- language profiles;
- script rendering metadata;
- charset range utilities.

Important files:

- `fontshow/ontology/language_tables.py`
- `fontshow/ontology/unicode_tables.py`
- `fontshow/unicode/charset_ranges.py`

---

## How one font entry moves through the system

A single font face starts in `fontshow/cli/dump_fonts.py`.

### Stage 1: discovery and raw extraction

`dump-fonts`:

- discovers font files;
- runs fontTools extraction;
- optionally merges Fontconfig metadata;
- builds one canonical descriptor per face via
  `fontshow/inventory/font_descriptor.py`.

At this point the descriptor is still raw.

It mainly contains:

- extracted metadata from the font binary;
- optional Fontconfig-derived fields;
- platform/runtime metadata;
- low-level per-face properties.

### Stage 2: parsing and enrichment

`parse-inventory` reads the raw inventory and processes each font entry in place.

The main enrichment path is coordinated in `fontshow/cli/parse_inventory.py`
and `fontshow/inventory/metadata_processing.py`.

The typical sequence is:

1. schema and structural checks;
2. charset decoding and normalization;
3. Unicode block derivation;
4. script inference;
5. language inference;
6. language normalization;
7. structured warning attachment;
8. specimen generation.

Important helper modules involved:

- `fontshow/unicode/charset_ranges.py`
- `fontshow/inventory/script_analysis.py`
- `fontshow/inventory/infer_languages.py`
- `fontshow/inventory/semantic_validation.py`
- `fontshow/inventory/specimens.py`
- `fontshow/core/warnings.py`

After this stage, the entry is enriched.

It now includes, in usable form:

- normalized coverage metadata;
- inferred scripts and languages;
- language normalization output;
- structured warning records;
- selected specimen text.

### Stage 3: validation

Validation may occur explicitly through `validate-inventory` or implicitly
through later pipeline assumptions.

This stage applies:

- schema validation;
- structural validation;
- semantic validation.

Key files:

- `fontshow/inventory/schema_validation.py`
- `fontshow/inventory/validation.py`
- `fontshow/inventory/semantic_validation.py`

### Stage 4: catalog generation

`create-catalog` loads the enriched inventory and hands the font list to
catalog helpers.

`fontshow/catalog/document.py` then:

- selects the primary script;
- chooses the render policy;
- selects fontspec and Polyglossia options;
- formats specimen output;
- assembles the final LaTeX blocks.

Other important helpers:

- `fontshow/catalog/pipeline.py`
- `fontshow/latex/render.py`
- `fontshow/latex/policy.py`
- `fontshow/latex/templates.py`

### State transitions summary

A font face moves through these states:

1. discovered filesystem font
2. raw canonical inventory record
3. enriched inventory record
4. catalog-facing render record
5. LaTeX block in the final document

---

## Change map

| Change area             | Primary files                                 | Why these files                      | Likely tests                                           |
|-------------------------|-----------------------------------------------|--------------------------------------|--------------------------------------------------------|
| Raw inventory shape     | `fontshow/inventory/font_descriptor.py`,      | Descriptor construction,             | `tests/test_validate_font_entry.py`,                   |
|                         | `fontshow/inventory/types.py`,                | shared typed structures, and         | `tests/test_validate_inventory.py`,                    |
|                         | `fontshow/core/types.py`,                     | schema contract are defined here.    | `tests/schema/test_inventory_schema_validation.py`,    |
|                         | `fontshow/schema/inventory_v1_2.json`         |                                      | `tests/schema/test_schema_validation.py`               |
| Charset normalization   | `fontshow/unicode/charset_ranges.py`,         | Charset decode, range normalization, | `tests/test_charset_decoding.py`,                      |
|                         | `fontshow/inventory/metadata_processing.py`,  | and block derivation happen here.    | `tests/test_charset_normalization.py`,                 |
|                         | `fontshow/platform/fontconfig.py`             |                                      | `tests/test_charset_to_script_coverage.py`,            |
|                         |                                               |                                      | `tests/schema/test_schema_validation_charset.py`       |
| Script inference        | `fontshow/inventory/script_analysis.py`,      | Heuristics and script-range          | `tests/test_infer_scripts.py`,                         |
|                         | `fontshow/ontology/unicode_tables.py`         | knowledge are centralized here.      | `tests/test_charset_to_script_coverage.py`             |
| Language inference      | `fontshow/inventory/infer_languages.py`,      | Candidate scoring and                | `tests/test_infer_languages.py`,                       |
| thresholds              | `fontshow/ontology/language_tables.py`        | ontology-backed language profiles    | `tests/test_infer_languages_threshold.py`,             |
|                         |                                               | live here.                           | `tests/test_parse_inventory_integration.py`            |
| Language normalization  | `fontshow/inventory/semantic_validation.py`,  | Normalization, dropped/deprecated    | `tests/test_language_normalization.py`,                |
| and semantic language   | `fontshow/core/warnings.py`                   | handling, and structured warnings    | `tests/test_validate_language_codes.py`,               |
| checks                  |                                               | are here.                            | `tests/test_semantic_validation.py`,                   |
|                         |                                               |                                      | `tests/test_strict_semantic.py`                        |
| Inventory parsing flow  | `fontshow/cli/parse_inventory.py`,            | The parse CLI and in-place           | `tests/test_parse_inventory_integration.py`,           |
|                         | `fontshow/inventory/metadata_processing.py`,  | enrichment path are coordinated      | `tests/test_parse_inventory_logging.py`,               |
|                         | `fontshow/inventory/io.py`                    | here.                                | `tests/cli/test_parse-inventory.py`                    |
| Schema validation       | `fontshow/inventory/schema_validation.py`,    | Public and strict schema validation  | `tests/schema/test_inventory_schema_validation.py`,    |
| behavior                | `fontshow/schema/inventory_v1_2.json`         | are implemented here against the     | `tests/schema/test_schema_validation.py`,              |
|                         |                                               | bundled schema.                      | `tests/schema/test_schema_validation_regression.py`    |
| General inventory       | `fontshow/inventory/validation.py`,           | Structural checks outside pure       | `tests/test_validate_font_entry.py`,                   |
| validation              | `fontshow/inventory/entry_validation.py`      | JSON-schema validation live here.    | `tests/test_validate_inventory.py`                     |
| Specimen generation     | `fontshow/inventory/specimens.py`,            | Inventory-level specimen fallback    | Indirectly covered by                                  |
|                         | `fontshow/common/specimens.py`                | and shared sample selection live     | `tests/test_parse_inventory_integration.py`,           |
|                         |                                               | here.                                | `tests/test_output_schema_invariants.py`               |
| Catalog filtering       | `fontshow/catalog/pipeline.py`,               | Input inventory loading, family      | `tests/test_cli_invariants.py`,                        |
| and grouping            | `fontshow/inventory/io.py`,                   | grouping, test-font filtering, and   | `tests/test_artifact_hygiene.py`,                      |
|                         | `fontshow/cli/create_catalog.py`              | orchestration happen here.           | `tests/test_deterministic_output.py`,                  |
|                         |                                               |                                      | `tests/test_platform_strictness.py`                    |
| Catalog rendering       | `fontshow/catalog/document.py`,               | Entry block rendering, escaping,     | `tests/test_deterministic_output.py`,                  |
| and LaTeX layout        | `fontshow/catalog/labels.py`,                 | policy selection, and templates are  | `tests/test_artifact_hygiene.py`,                      |
|                         | `fontshow/latex/render.py`,                   | all separated here.                  | `tests/test_cli_invariants.py`                         |
|                         | `fontshow/latex/policy.py`,                   |                                      |                                                        |
|                         | `fontshow/latex/templates.py`                 |                                      |                                                        |
| JSON serialization /    | `fontshow/core/json_format.py`,               | Pretty-printing and enum             | `tests/test_enum_json_boundary.py`,                    |
| enum boundary           | `fontshow/core/json_boundary.py`              | normalization across disk/in-memory  | `tests/test_json_formatting.py`,                       |
|                         |                                               | boundaries are here.                 | `tests/test_output_schema_invariants.py`               |
| Logging behavior        | `fontshow/core/logging_utils.py`,             | Structured logging, TRACE support,   | `tests/test_fc_query_logging.py`,                      |
|                         | `fontshow/core/cli_utils.py`                  | and CLI-visible logging helpers      | `tests/test_trace_logging.py`,                         |
|                         |                                               | live here.                           | `tests/test_parse_inventory_logging.py`,               |
|                         |                                               |                                      | `tests/cli/test_cli_quiet_verbose.py`                  |
| CLI dispatch            | `fontshow/__main__.py`,                       | Top-level dispatch and per-command   | `tests/cli/test_create-catalog.py`,                    |
| and exit codes          | `fontshow/cli/create_catalog.py`,             | wrapper semantics are defined here.  | `tests/cli/test_dump-fonts.py`,                        |
|                         | `fontshow/cli/dump_fonts.py`,                 |                                      | `tests/cli/test_parse-inventory.py`,                   |
|                         | `fontshow/cli/parse_inventory.py`,            |                                      | `tests/cli/test_fontshow_version.py`                   |
|                         | `fontshow/cli/validate_inventory.py`          |                                      |                                                        |
| Preflight checks        | `fontshow/preflight/runner.py`,               | Check registration, execution,       | `tests/preflight/test_registry.py`,                    |
| and policy              | `fontshow/preflight/model.py`,                | result modeling, and policy logic    | `tests/preflight/test_base_check_contract.py`,         |
|                         | `fontshow/preflight/render.py`,               | are all here.                        | `tests/preflight/test_environment_policy.py`,          |
|                         | `fontshow/preflight/checks/base.py`,          |                                      | `tests/preflight/test_environment_matrix.py`,          |
|                         | `fontshow/preflight/checks/environment.p y`,  |                                      | `tests/preflight/test_font_discovery_policy.py`,       |
|                         | `fontshow/preflight/checks/font_discovery.py`,|                                      | `tests/preflight/test_latex_policy.py`,                |
|                         | `fontshow/preflight/checks/latex.py`,         |                                      | `tests/preflight/test_render.py`                       |
|                         | `fontshow/preflight/checks/ontology.py`       |                                      |                                                        |
| Preflight CLI behavior  | `fontshow/preflight/__main__.py`              | Standalone preflight CLI wiring,     | `tests/cli/test_preflight_cli.py`,                     |
|                         |                                               | output file handling, and exit-code  | `tests/cli/test_preflight_output_file.py`,             |
|                         |                                               | conversion are here.                 | `tests/preflight/test_preflight_internal_exception.py` |

  If you want, I can also normalize this same table for the other two maps so they all share the same multiline style.

---

## Ripple-risk map

| Change area             | Safe starting point                         | Ripple risk | Common downstream modules affected            |
|-------------------------|---------------------------------------------|-------------|-----------------------------------------------|
| Font discovery behavior | `fontshow/platform/font_discovery.py`       | Medium      | `fontshow/cli/dump_fonts.py`,                 |
|                         |                                             |             | `fontshow/platform/fontconfig.py`,            |
|                         |                                             |             | `fontshow/inventory/fonttools_extraction.py`  |
| Raw inventory shape     | `fontshow/inventory/font_descriptor.py`     | High        | `fontshow/cli/parse_inventory.py`,            |
|                         |                                             |             | `fontshow/inventory/validation.py`,           |
|                         |                                             |             | `fontshow/catalog/document.py`,               |
|                         |                                             |             | `fontshow/schema/inventory_v1_2.json`         |
| Charset normalization   | `fontshow/unicode/charset_ranges.py`        | Medium      | `fontshow/inventory/metadata_processing.py`,  |
|                         |                                             |             | `fontshow/inventory/script_analysis.py`,      |
|                         |                                             |             | `fontshow/inventory/infer_languages.py`       |
| Script inference        | `fontshow/inventory/script_analysis.py`     | Medium      | `fontshow/inventory/metadata_processing.py`,  |
|                         |                                             |             | `fontshow/catalog/document.py`,               |
|                         |                                             |             | `fontshow/latex/policy.py`                    |
| Language inference      | `fontshow/inventory/infer_languages.py`     | Medium      | `fontshow/inventory/metadata_processing.py`,  |
| thresholds              |                                             |             | `fontshow/inventory/semantic_validation.py`,  |
|                         |                                             |             | `fontshow/common/specimens.py`                |
| Language normalization  | `fontshow/inventory/semantic_validation.py` | High        | `fontshow/core/warnings.py`,                  |
| and semantic checks     |                                             |             | `fontshow/cli/parse_inventory.py`,            |
|                         |                                             |             | `fontshow/cli/create_catalog.py`,             |
|                         |                                             |             | `fontshow/diagnostics/inventory_warnings.py`  |
| Inventory parsing flow  | `fontshow/cli/parse_inventory.py`           | High        | `fontshow/inventory/metadata_processing.py`,  |
|                         |                                             |             | `fontshow/inventory/schema_validation.py`,    |
|                         |                                             |             | `fontshow/inventory/specimens.py`             |
| Schema validation       | `fontshow/inventory/schema_validation.py`   | High        | `fontshow/cli/validate_inventory.py`,         |
| behavior                |                                             |             | `fontshow/cli/parse_inventory.py`,            |
|                         |                                             |             | `fontshow/inventory/validation.py`            |
| General inventory       | `fontshow/inventory/validation.py`          | Medium      | `fontshow/cli/validate_inventory.py`,         |
| validation              |                                             |             | `fontshow/cli/create_catalog.py`,             |
|                         |                                             |             | `fontshow/inventory/entry_validation.py`      |
| Specimen generation     | `fontshow/inventory/specimens.py`           | Medium      | `fontshow/common/specimens.py`,               |
|                         |                                             |             | `fontshow/catalog/document.py`                |
| Catalog filtering       | `fontshow/catalog/pipeline.py`              | Medium      | `fontshow/cli/create_catalog.py`,             |
| and grouping            |                                             |             | `fontshow/inventory/io.py`,                   |
|                         |                                             |             | `fontshow/catalog/document.py`                |
| Catalog rendering       | `fontshow/catalog/document.py`              | High        | `fontshow/catalog/labels.py`,                 |
| and LaTeX layout        |                                             |             | `fontshow/latex/render.py`,                   |
|                         |                                             |             | `fontshow/latex/policy.py`                    |
| JSON serialization /    | `fontshow/core/json_boundary.py`            | Low         | `fontshow/core/json_format.py`,               |
| enum boundary           |                                             |             | `fontshow/cli/parse_inventory.py`,            |
|                         |                                             |             | `fontshow/cli/dump_fonts.py`                  |
| Logging behavior        | `fontshow/core/logging_utils.py`            | Medium      | `fontshow/core/cli_utils.py`,                 |
|                         |                                             |             | `fontshow/platform/fontconfig.py`,            |
|                         |                                             |             | `fontshow/cli/parse_inventory.py`,            |
|                         |                                             |             | `fontshow/preflight/runner.py`                |
| CLI dispatch            | `fontshow/__main__.py`                      | Medium      | all command modules under `fontshow/cli`,     |
| and exit codes          |                                             |             | `fontshow/preflight/__main__.py`              |
| Preflight checks        | `fontshow/preflight/checks/environment.py`  | Medium      | `fontshow/preflight/runner.py`,               |
| and policy              | or another specific check module            |             | `fontshow/preflight/model.py`,                |
|                         |                                             |             | `fontshow/preflight/render.py`                |
| Preflight CLI behavior  | `fontshow/preflight/__main__.py`            | Low         | `fontshow/preflight/runner.py`,               |
|                         |                                             |             | `fontshow/preflight/render.py`,               |
|                         |                                             |             | `fontshow/core/cli_utils.py`                  |

---

## Bug triage map

| Symptom                  | Most likely module        | First files to inspect                         |
|--------------------------|---------------------------|------------------------------------------------|
| `fontshow` command exits | CLI dispatch              | `fontshow/__main__.py`,                        |
| with wrong code or wrong |                           | `fontshow/core/cli_utils.py`                   |
| subcommand behavior      |                           |                                                |
| `preflight` says         | Preflight environment     | `fontshow/preflight/checks/environment.py`,    |
| environment unsupported  | policy                    | `fontshow/preflight/runner.py`                 |
| unexpectedly             |                           |                                                |
| `preflight` cannot find  | Preflight capability      | `fontshow/preflight/checks/font_discovery.py`, |
| `fc-list` or LuaLaTeX    | checks                    | `fontshow/preflight/checks/latex.py`           |
| `dump-fonts` finds no    | Platform discovery        | `fontshow/platform/font_discovery.py`,         |
| fonts or too few fonts   |                           | `fontshow/cli/dump_fonts.py`                   |
| `dump-fonts` drops valid | Face filtering /          | `fontshow/inventory/fonttools_extraction.py`,  |
| fonts as unsupported     | extraction                | `fontshow/inventory/validation.py`,            |
|                          |                           | `fontshow/cli/dump_fonts.py`                   |
| Fontconfig metadata is   | Fontconfig integration    | `fontshow/platform/fontconfig.py`,             |
| missing or malformed     |                           | `fontshow/cli/dump_fonts.py`                   |
| Inventory JSON shape     | Descriptor construction / | `fontshow/inventory/font_descriptor.py`,       |
| changed or fields are    | schema                    | `fontshow/schema/inventory_v1_2.json`,         |
| missing unexpectedly     |                           | `fontshow/core/types.py`                       |
| `parse-inventory` fails  | Parse orchestration or    | `fontshow/cli/parse_inventory.py`,             |
| on valid input           | schema validation         | `fontshow/inventory/schema_validation.py`,     |
|                          |                           | `fontshow/inventory/io.py`                     |
| Languages are missing or | Language inference        | `fontshow/inventory/infer_languages.py`,       |
| look too conservative    | thresholds                | `fontshow/ontology/language_tables.py`         |
| Scripts are wrong or     | Script inference          | `fontshow/inventory/script_analysis.py`,       |
| `"unknown"` appears      |                           | `fontshow/ontology/unicode_tables.py`          |
| unexpectedly             |                           |                                                |
| Charset ranges or        | Charset normalization     | `fontshow/unicode/charset_ranges.py`,          |
| Unicode blocks look      |                           | `fontshow/inventory/metadata_processing.py`    |
| wrong                    |                           |                                                |
| Language tags are        | Semantic normalization    | `fontshow/inventory/semantic_validation.py`,   |
| dropped, normalized, or  |                           | `fontshow/core/warnings.py`                    |
| warned unexpectedly      |                           |                                                |
| Specimen text is empty,  | Specimen selection        | `fontshow/inventory/specimens.py`,             |
| ugly, or from the wrong  |                           | `fontshow/common/specimens.py`,                |
| language                 |                           | `fontshow/catalog/document.py`                 |
| `validate-inventory`     | Schema or semantic        | `fontshow/inventory/schema_validation.py`,     |
| rejects data             | validation                | `fontshow/inventory/validation.py`,            |
| unexpectedly             |                           | `fontshow/inventory/semantic_validation.py`    |
| `create-catalog` rejects | Platform compatibility    | `fontshow/platform/runtime.py`,                |
| an inventory due to      | enforcement               | `fontshow/cli/create_catalog.py`               |
| platform mismatch        |                           |                                                |
| Catalog output is        | Catalog pipeline / JSON   | `fontshow/catalog/pipeline.py`,                |
| nondeterministic         | ordering / grouping       | `fontshow/catalog/document.py`,                |
|                          |                           | `fontshow/core/json_format.py`                 |
| LaTeX output is broken   | Catalog rendering /       | `fontshow/catalog/document.py`,                |
| or escaping is wrong     | LaTeX helpers             | `fontshow/latex/render.py`,                    |
|                          |                           | `fontshow/latex/templates.py`                  |
| Wrong script-specific    | LaTeX render policy       | `fontshow/latex/policy.py`,                    |
| render policy or         |                           | `fontshow/ontology/language_tables.py`         |
| Polyglossia usage        |                           |                                                |
| Warning severities       | JSON boundary             | `fontshow/core/json_boundary.py`,              |
| serialize incorrectly or |                           | `fontshow/core/json_format.py`                 |
| JSON roundtrip changes   |                           |                                                |
| meaning                  |                           |                                                |
| TRACE or DEBUG logs are  | Logging facade            | `fontshow/core/logging_utils.py`,              |
| missing / attributed to  |                           | `fontshow/platform/fontconfig.py`,             |
| wrong caller             |                           | `fontshow/cli/parse_inventory.py`              |

---

## Practical reading order

For a new contributor, this is the most efficient order:

1. `fontshow/__main__.py`
2. `fontshow/cli/dump_fonts.py`
3. `fontshow/cli/parse_inventory.py`
4. `fontshow/cli/create_catalog.py`
5. `fontshow/preflight/__main__.py`
6. then the subsystem files relevant to the feature or bug you care about

This order gives you:

- the CLI surface;
- the main data flow;
- the handoff points between discovery, enrichment, validation, and rendering.
