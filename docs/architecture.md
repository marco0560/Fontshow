# Architecture

## Overview

Fontshow is a font inventory and catalog generation toolchain designed as
a linear, data-driven pipeline.

Each stage of the pipeline consumes structured data produced by the
previous stage and enriches or transforms it without side effects outside
its responsibility.

At a high level, Fontshow consists of three main stages:

1. **Font discovery and raw metadata extraction**
2. **Semantic inference and normalization**
3. **Catalog generation and rendering**

The architecture intentionally avoids tight coupling between stages and
relies on explicit data contracts instead of shared state.

## Repository Layout

The Fontshow repository is organized as follows:

- `src/fontshow/`
  Core Fontshow package. Contains the stable implementation of the pipeline,
  including preflight checks, validation logic, and CLI entry points.

- `tests/`
  Automated test suite covering core functionality, preflight policies,
  CLI behavior, and validation logic.

- `docs/`
  Project documentation, including architecture notes, pipeline design,
  CLI usage, design decisions, and development guidelines.

- `scripts/`
  Development and maintenance scripts used by project maintainers.
  These scripts are **not part of the public API** and are not required for
  normal Fontshow usage.

- `pyproject.toml`
  Project configuration, dependencies, and tooling configuration.

- `mkdocs.yml`
  Documentation build configuration.

- `CHANGELOG.md`
  Automatically generated changelog maintained by semantic-release.

For details about development-only tooling, see
[Development scripts](scripts.md).

## Python package subdivision

The `src/fontshow/` package is intentionally subdivided by responsibility.

This subdivision mirrors the pipeline stages and the project's
cross-cutting infrastructure. The goal is to keep orchestration,
domain logic, platform integration, and rendering concerns clearly
separated.

### `fontshow.cli`

Contains command orchestration for the public CLI.

Responsibilities:

- parse and validate command arguments;
- coordinate workflow stages;
- return deterministic process exit codes;
- delegate business logic to lower-level subsystems.

This package is the boundary between the user-facing CLI and the
internal pipeline implementation.

### `fontshow.preflight`

Contains the environment validation subsystem executed before the main
pipeline.

Responsibilities:

- detect runtime environment characteristics;
- check availability of required external tools;
- aggregate check results;
- render preflight output for CLI consumption.

This package is intentionally isolated from inventory and catalog logic.

### `fontshow.platform`

Contains platform- and tool-specific integration code.

Responsibilities:

- discover installed fonts on supported operating systems;
- query system font metadata providers such as Fontconfig;
- compare stored and current runtime platform metadata.

This package is the main boundary for environment-dependent behavior.

### `fontshow.inventory`

Contains the inventory domain model and all inventory-side processing.

Responsibilities:

- construct canonical raw font descriptors;
- load and validate inventory structures;
- normalize charset data;
- infer scripts and languages;
- attach semantic warnings;
- generate specimen metadata.

This package is the core of the data pipeline and acts on JSON-like
inventory structures rather than user-facing CLI state.

### `fontshow.catalog`

Contains catalog-domain helpers used to transform enriched inventory
entries into catalog-ready records and LaTeX document fragments.

Responsibilities:

- group and filter font entries for catalog generation;
- choose sample text and labels for display;
- assemble the final catalog document.

This package is concerned with presentation-oriented transformation,
not discovery or inference.

### `fontshow.latex`

Contains low-level LaTeX rendering support.

Responsibilities:

- escape and sanitize LaTeX content;
- define rendering policies for different scripts;
- provide reusable LaTeX templates and formatting helpers.

This package isolates rendering mechanics from catalog orchestration.

### `fontshow.core`

Contains shared infrastructure reused across multiple subsystems.

Responsibilities:

- shared CLI utilities;
- logging facade and TRACE support;
- JSON formatting and enum boundary helpers;
- structured warning helpers;
- shared type definitions and global constants.

This package must remain broadly reusable and avoid subsystem-specific
business logic.

### `fontshow.constants`

Contains grouped constant sets used across the project.

Responsibilities:

- runtime-wide constant values;
- catalog-specific constants;
- OpenType-related identifiers.

This package exists to make stable constant sources explicit and
centralized.

### `fontshow.ontology`

Contains authoritative static knowledge tables used by inference and
rendering logic.

Responsibilities:

- language metadata profiles;
- script metadata profiles;
- Unicode-derived ontology tables.

This package is read-only reference data, not workflow orchestration.

### `fontshow.unicode`

Contains Unicode-specific transformation helpers.

Responsibilities:

- normalize charset ranges;
- derive Unicode block coverage;
- decode compact charset representations from external sources.

This package provides foundational Unicode utilities used by the
inventory subsystem.

### `fontshow.common`

Contains small reusable domain helpers shared across higher-level
packages.

At present this package mainly hosts specimen-related helpers that are
shared between the inventory and catalog domains without belonging
entirely to either one.

### Lightweight namespace packages

Some packages currently act mainly as namespace and layering markers,
including:

- `fontshow.discovery`
- `fontshow.json`
- `fontshow.logging`
- `fontshow.schema`

These packages still serve an architectural purpose: they preserve
explicit subsystem boundaries and provide stable import locations for
future growth.

## Design principles

Fontshow follows a small set of explicit design principles:

- **Inventory-driven**
  All decisions are based on serialized inventory data.
  No stage reopens or re-inspects font binaries unnecessarily.

- **Procedural and explicit**
  The code favors explicit data flow over abstraction layers.

- **Best-effort robustness**
  Partial failures should degrade output quality, not abort execution.

- **Separation of concerns**
  Discovery, inference, and rendering are strictly separated.

- **Reproducibility**
  Given the same inventory input, downstream stages produce identical
  results.

## Pipeline overview

The Fontshow pipeline is strictly linear:

```text
Installed fonts
      │
      ▼
fontshow dump-fonts
      │   (raw inventory JSON)
      ▼
fontshow parse-inventory
      │   (enriched inventory JSON)
      ▼
fontshow create-catalog
      │
      ▼
LaTeX catalog
```

Each stage produces a JSON-compatible structure that can be:

- inspected manually,
- cached,
- reused independently of the other stages.

## Data flow and contracts

The central artifact in Fontshow is the **font inventory**.

The inventory is a JSON document with two main sections:

- `metadata`: global information about the generation context
- `fonts`: a list of per-font (or per-face) descriptors

Metadata fields may include environment and tool information intended for
debugging and reproducibility purposes. Downstream stages must treat metadata
as informative and non-authoritative.

Each stage respects the following contract:

- **fontshow dump-fonts**
  Produces *raw*, low-level metadata directly extracted from font files
  and system tools.

- **fontshow parse-inventory**
  Adds semantic interpretation (scripts, languages, coverage inference)
  without modifying raw fields.

- **fontshow create-catalog**
  Treats the inventory as read-only input and performs rendering only.

Downstream stages must never assume the presence of optional fields unless
explicitly documented.

### Font Descriptor Contract (Dump Phase)

The `dump_fonts` stage produces *raw font descriptors* that follow a strict
contract. This contract defines what information must be present, what may be
missing, and how incomplete data is handled.

#### Identity

- `identity.file` (**required**)
  Absolute or canonical path of the font file. Its absence is considered a
  fatal error.
- `identity.family` (**optional, warned**)
  The typographic family name. Fonts lacking a family name are accepted but
  generate a warning.

#### Scripts Coverage

- `coverage.scripts` (**optional, warned**)
  Script information as reported by FontConfig. The field may be empty when
  FontConfig is unavailable or the font does not expose script metadata.

#### Sample Text

- `sample_text` (**optional**)
  Treated as *content*, not metadata. Intended for downstream consumers such
  as `create_catalog`, and not used for font identification or inference.

#### Error vs Warning Policy

- Missing mandatory identity fields (e.g. `identity.file`) are fatal.
- Missing semantic fields (e.g. family name, scripts) generate warnings but do
  not prevent inventory generation.

This contract intentionally separates *observation* (dump phase) from
*interpretation* (parse/inference phase).

### Coverage vs Inference Semantics

Fontshow distinguishes strictly between *coverage* and *inference* data.

#### Coverage

 represents raw observations gathered from font files or external
tools (e.g. FontConfig). Coverage data is:

- incomplete and tool-dependent,
- never corrected or normalized,
- allowed to be missing or empty.

Examples of coverage data include Unicode ranges, Unicode blocks, raw script
information reported by FontConfig, and sample text extracted from the font.

**Inference** represents Fontshow’s interpretation of coverage and metadata.
Inference data is:

- normalized and consistent,
- independent from the original tool,
- guaranteed to be present in a usable form.

For example, inferred script lists are always present and use ISO 15924 tags.
When no script can be inferred, the special value `"unknown"` is used.

The value `"unknown"` is never emitted in coverage data and only appears as the
result of inference.

### FontConfig charset integration

Fontshow can optionally enrich the font inventory with Unicode charset
information provided by Fontconfig using the option
`--include-fc-charset` in the `dump_fonts` tool.

Fontconfig charset data:

- represents *advertised* Unicode coverage
- is provided as compact Unicode ranges
- is considered a secondary, non-authoritative source

The primary source of Unicode coverage in Fontshow remains the
`coverage` field computed via FontTools.

The integration is optional, non-breaking, and designed for future
extensions of the inventory schema.

## Module responsibilities

### dump_fonts

Responsible for:

- discovering installed font files,
- extracting per-face metadata using fontTools,
- optional enrichment via FontConfig (Linux),
- caching expensive extraction results.

It does **not**:

- perform semantic inference,
- group fonts,
- make rendering decisions.

### fontshow parse-inventory

Responsible for:

- interpreting Unicode coverage,
- inferring scripts and languages,
- normalizing and enriching inventory entries.

It operates purely on structured data and never accesses font binaries.

### create_catalog

Responsible for:

- grouping fonts by family,
- selecting representative samples,
- rendering LaTeX source code.

It does not perform inference and does not alter the inventory semantics.

## Error handling and robustness

Fontshow adopts a best-effort error handling strategy:

- errors are captured locally whenever possible,
- partial failures are represented explicitly in the data,
- the pipeline continues unless a critical invariant is violated.

This approach ensures that:

- large font collections remain processable,
- malformed fonts do not abort the entire run,
- diagnostic information remains available for inspection.

## CLI architecture and testability

Fontshow CLI commands are designed to be **fully testable, deterministic, and
independent from the host environment**.
To achieve this, all CLI commands follow a **strict layered architecture**
that clearly separates:

- user-facing CLI behavior
- test seams
- core business logic

This design guarantees correct exit codes, stable CLI tests, and preservation
of all official entrypoints (including `python -m fontshow`,
`python -m fontshow.preflight`, and module-backed commands such as
`python -m fontshow.cli.dump_fonts`,
`python -m fontshow.cli.parse_inventory`,
`python -m fontshow.cli.validate_inventory`, and
`python -m fontshow.cli.create_catalog`).

---

### Layered CLI structure

Each CLI command follows the same three-layer pattern:

1. **Core function (`run_<command>`)**
   - Contains all business logic
   - Performs filesystem I/O and processing
   - Returns an integer exit code
   - MUST NOT call `sys.exit()`
   - SHOULD NOT print user-facing messages

2. **Indirection layer (`_run_<command>`)**
   - Thin wrapper around the core function
   - Exists exclusively for CLI testing
   - Is the only function monkeypatched in CLI tests
   - Provides a stable test seam without touching business logic

3. **CLI entrypoint (`main(args)`)**
   - Receives parsed arguments from the dispatcher
   - Calls the indirection layer
   - Handles exceptions and maps them to exit codes
   - Produces user-facing output
   - Returns an integer exit code

This structure is applied uniformly to all commands:

- `preflight`
- `dump-fonts`
- `parse-inventory`
- `create-catalog`

---

### Rationale

This design deliberately avoids:

- monkeypatching internal business logic
- reliance on default arguments bound at function definition time
- accidental coupling between tests and implementation details

It guarantees:

- stable and predictable exit codes
- fully isolated and deterministic CLI tests
- preservation of all CLI entrypoints
- consistent behavior across all commands

---

### CLI testing isolation principle

All CLI-level tests **must be environment-independent**.

In particular, CLI tests MUST NOT depend on:

- LaTeX availability
- installed system fonts
- Fontconfig presence
- OS-specific behavior
- CI vs local environment differences

Instead, CLI tests MUST stub command execution by monkeypatching the
appropriate indirection layer (e.g. `_run_<command>`).

The purpose of CLI tests is strictly to validate:

- argument parsing
- exit codes
- user-visible output
- option behavior (`--quiet`, `--verbose`, `--version`, defaults)

Environment capability checks (LaTeX, fonts, OS support) are validated
exclusively by:

- unit tests of the corresponding modules
- preflight unit and integration tests

This separation ensures:

- deterministic CLI tests
- stable CI execution
- clear responsibility boundaries between layers

---

### CLI testing architecture

Fontshow CLI commands are tested through the **real CLI entrypoint**
(`fontshow.__main__.main`) using a shared `cli_runner` fixture.

Key design principles:

1. **Real entrypoint execution**
   CLI tests execute the real `main()` function instead of calling helpers
   directly, ensuring realistic coverage of argument parsing and dispatch.

2. **Deterministic stubbing**
   External dependencies are stubbed via pytest fixtures by monkeypatching
   symbols **as imported by the CLI module**, not by patching deep internals.

3. **Result-driven exit codes**
   CLI exit codes are derived exclusively from explicit return values or
   controlled exceptions, never from implicit side effects.

4. **CI-safe behavior**
   Tests never depend on the actual runtime environment. All environment-
   dependent logic is stubbed.

5. **Minimal result contracts**
   Stubbed objects implement only the minimal interface required by the CLI,
   ensuring long-term test stability and maintainability.

---

This architecture guarantees:

- reproducible CLI tests
- isolation from host environment
- clean separation between command orchestration and domain logic
- a scalable pattern for future CLI commands

## Why a procedural architecture

Fontshow intentionally avoids a class-based or object-oriented architecture.

Reasons include:

- the pipeline is naturally linear and data-driven,
- the primary abstraction is the **inventory**, not behavior,
- procedural code makes data transformations explicit and traceable,
- it aligns well with batch-style processing and reproducibility.

This choice prioritizes clarity and debuggability over extensibility through
inheritance.

### Inventory schema evolution

Fontshow uses a versioned JSON inventory as the central data contract
between pipeline stages.

Each inventory declares a `schema_version` in its metadata. Downstream
stages must remain tolerant to missing or unknown fields and must not
assume the presence of optional metadata.

## Non-goals and future extensions

Fontshow explicitly does not aim to:

- be a font management application,
- provide interactive UI components,
- replace existing font inspection tools.

Possible future extensions include:

- additional output formats (HTML, PDF),
- richer statistical summaries,
- external inventory consumers.

These extensions can be implemented without altering the core pipeline.
