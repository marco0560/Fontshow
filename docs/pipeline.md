# Fontshow Pipeline

## Overview

This document describes the Fontshow processing pipeline, from font discovery to catalog creation.

The pipeline is designed as a **sequence of distinct stages**, each with a distinct responsibility.
Understanding stage boundaries is essential for debugging, validation, and
environment-related issue analysis.

The goal of the pipeline is to:
- collect information about fonts installed on the system;
- normalize and validate this information;
- produce a final, usable catalog (currently in LaTeX format).

The guiding principle is **separation of concerns**: each stage can be executed, verified, and debugged independently.

## Execution Environment

The pipeline described in this document assumes execution within a
well-defined environment.

Supported, partial, and experimental environments are documented separately
in [`environment-matrix.md`](environment-matrix.md).

Environmental mismatches are a common source of pipeline failures and should
be evaluated before investigating application-level issues.

## General Flow

The logical pipeline can be summarized as:

<!-- cheatsheet:start -->
```
Preflight checks
  ↓
System font dump
  ↓
Inventory parsing, validation and enrichment
  ↓
Catalog creation (.tex generation)
  ↓
LuaLaTeX compilation (multi-pass)
```
<!-- cheatsheet:end -->

Each stage produces one or more intermediate artifacts, which can be retained for later analysis.

## Stage 0 — Preflight Checks

### Purpose

The preflight stage validates that the execution environment satisfies the
minimum requirements needed to run the Fontshow pipeline safely.

Its primary goals are to:
- detect missing or incompatible system-level dependencies early,
- distinguish environment-related issues from application-level failures,
- fail fast with clear diagnostics when execution cannot proceed meaningfully.

Preflight checks are intentionally conservative and do not attempt to fix or
work around detected issues.

### Scope

Preflight checks are limited to environment validation and capability detection.

They do not:
- inspect or modify user data,
- parse or validate font inventories,
- perform font discovery,
- run LaTeX compilations,
- execute any pipeline stage beyond basic environment inspection.

All data processing and validation remain the responsibility of subsequent
pipeline stages.

### Supported environments

The preflight stage classifies execution environments according to their level
of support:

- **Linux (bare metal)**: fully supported and considered the reference environment.
- **Linux VM / WSL / container / chroot**: supported with limitations; additional
  warnings may be emitted.
- **Windows 11**: experimental support; execution is allowed but not fully guaranteed.
- **macOS**: not supported in the current version; support is planned for a future
  v2.x.y release.

### Checks performed

The preflight stage performs a fixed set of checks, including:

- detection of the operating system and execution mode,
- verification of a supported font discovery backend being available,
- verification of the required LuaLaTeX engine,
- detection of potential mismatches between font discovery and LaTeX compilation
  environments.

The exact checks executed may vary depending on the detected environment
(e.g. interactive execution versus CI).

### Severity levels

Each preflight check produces one of the following severity levels:

- **INFO**: contextual information useful for debugging; never blocks execution
  and is only shown when verbose output is enabled.
- **OK**: the requirement is satisfied.
- **WARN**: a known risk or limitation has been detected; execution is allowed
  but may lead to reduced functionality or failures in later stages.
- **ERROR**: a required capability is missing or incompatible; execution is
  aborted immediately.

The overall preflight result is derived from the most severe check outcome.
Informational results do not contribute to the overall preflight outcome.

### CLI behavior

By default, the CLI displays only warnings, errors, and the final preflight
summary.

When the `--verbose` flag is enabled, additional informational and successful
checks are displayed.

Warnings do not prevent execution, while errors always abort the pipeline with
a non-zero exit code.

The `--verbose` flag does not alter the execution flow or exit codes.

### CI behavior

When executed in a CI environment (such as GitHub Actions), the preflight stage
runs in a reduced mode tailored for non-interactive environments.

Checks that require access to real system fonts or a full LaTeX toolchain are
skipped and reported as informational output.

In CI, the preflight stage only fails on errors that indicate a misconfigured
runtime environment (e.g. unsupported Python version or invalid CLI usage).

## Stage 1 — System font dump

The first stage consists of collecting raw information about fonts installed on the system.

This stage:
- queries the system via `fontconfig`;
- collects font file paths and available metadata;
- **does not apply any normalization or correction**.

The result is a dump that faithfully reflects the state of the system at a specific point in time.

### Inventory representation

The font dump is transformed into a **structured inventory**, representing a coherent snapshot of system fonts.

Inventory characteristics:
- human-readable format;
- stable structure;
- absence of “silent corrections”.

The inventory may contain:
- incomplete data;
- non-normalized names;
- irregularities originating from the system.

This is intentional: the inventory describes reality, not an idealized version of it.

👉 For implementation details, see:
- [`dump-fonts`](tools/dump_fonts.md)

## Stage 2 — Inventory parsing, validation and enrichment

At this stage, the inventory is analyzed and transformed into richer data structures by applying additional analysis and inference steps.

Parsing:
- interprets individual inventory entries;
- associates fonts with their corresponding files;
- reports errors and anomalies.

### Inventory enrichment

Inventory enrichment operates exclusively on inventory data and does not interact
with system-level font discovery or rendering mechanisms.

This stage is responsible for:
- validating inventory structure and consistency,
- inferring additional properties from existing metadata,
- preparing the inventory for downstream consumption.

### Inventory validation

An explicit **validation mode** is available, which:
- identifies problematic entries;
- associates each error with the affected font path;
- allows deciding whether processing should stop or continue.

### Data normalization

After parsing, data is normalized to reduce ambiguity and inconsistency.

Normalization mainly concerns:
- font family names;
- styles (Regular, Bold, Italic, etc.);
- equivalent naming variations.

An important design choice is that:
- original values are **preserved**;
- normalized versions are **added**, not replaced.

This preserves traceability and facilitates debugging.

---

👉 Details in:
- [`parse-inventory`](tools/parse_font_inventory.md)

## Stage 3 — Catalog creation

The final stage of the pipeline is the creation of the final catalog, currently in **LaTeX** format.

At this stage:
- fonts that are effectively usable are selected;
- incompatible or problematic fonts are excluded or reported;
- a `.tex` file ready for compilation is generated.

It is normal that:
- the number of fonts in the final catalog is lower than in the initial dump;
- some fonts cause issues during LaTeX compilation.

👉 Details in:
- [`create-catalog`](tools/create_catalog.md)

## Stage 4 — LaTeX compilation

The final catalog is compiled using LuaLaTeX.

Although LuaLaTeX may require multiple compilation passes to resolve indices and
auxiliary constructs, this process is treated as a single logical stage in the
pipeline.

Failures at this stage may be caused by:
- missing or incomplete LaTeX toolchains,
- font rendering issues,
- environment mismatches between discovery and compilation.

## Pipeline artifacts

The pipeline produces several intermediate artifacts, including:
- font dumps;
- inventories;
- intermediate JSON files;
- final LaTeX files.

These artifacts:
- are not merely temporary outputs;
- can be used to compare different systems;
- facilitate testing, debugging, and validation.

## Environment considerations

Pipeline behavior may vary depending on the environment:
- native Linux;
- WSL;
- `fontconfig` configuration.

For this reason:
- some features are marked as *experimental*;
- full validation on native Linux is considered a required step.

## Links

For further details on individual components:

- General architecture:
  [`architecture.md`](architecture.md)

- Data dictionary:
  [`data_dictionary.md`](data_dictionary.md)

- Font dump:
  [`dump-fonts`](tools/dump_fonts.md)

- Inventory parsing:
  [`parse-inventory`](tools/parse_font_inventory.md)

- Catalog creation:
  [`create-catalog`](tools/create_catalog.md)

## Pipeline status

The pipeline is considered **functionally complete**, but still evolving with respect to:
- robustness across different environments;
- automated testing;
- handling of edge cases.

Open activities are tracked via **GitHub Issues**.
