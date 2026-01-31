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

```txt
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

## Pipeline Stages and Artifact Locality

Fontshow’s pipeline is composed of distinct stages with different assumptions
regarding execution environment and data locality.

Understanding these boundaries is essential for correct usage and for
interpreting validation results.

---

### Stage 1 — Preflight

Preflight validates that the *current execution environment* is suitable
for running subsequent stages.

This includes:

- availability of required tools
- expected runtime capabilities
- environment consistency

Preflight results are **not persisted** and are valid only for the system
on which they are executed.

---

### Stage 2 — dump-fonts

This stage:

- inspects the local filesystem
- queries the system font configuration
- discovers installed fonts
- produces a serialized inventory

This stage is **environment-dependent** and must be run on the system whose
fonts are being analyzed.

The resulting inventory is a **data artifact**, not a live reference.

---

### Stage 3 — parse-inventory

This stage operates **exclusively on serialized data**.

Important properties:

- No font files are accessed
- No filesystem paths are resolved
- No environment assumptions are made
- All paths are treated as opaque data

This means:

✔ The inventory JSON can be moved across machines
✔ The stage is safe to run on a different system
✔ No font files are required at this stage

This behavior is intentional and enforced by design.

---

### Stage 4 — create-catalog

This stage consumes the parsed inventory and produces catalog output.

While it does not re-scan fonts, it **assumes that path references contained
in the inventory are still meaningful** for the current environment.

As a result:

- Catalog generation may succeed across systems
- But path-based features depend on compatibility of environments
- No path normalization or remapping is performed

---

### Stage 5 — LaTeX Compilation

LaTeX compilation requires:

- actual access to font files
- correct font resolution by the TeX engine
- filesystem paths matching those recorded earlier

For this reason, LaTeX compilation **must be performed on the same system**
(or an equivalent environment) where fonts are available.

This is an intentional design constraint.

---

### Summary: Environment Assumptions

| Stage           | Requires Same Machine | Uses Filesystem | Portable |
|-----------------|-----------------------|-----------------|----------|
| Preflight       | ✔                     | ✔               | ❌       |
| dump-fonts      | ✔                     | ✔               | ❌       |
| parse-inventory | ❌                    | ❌              | ✔        |
| create-catalog  | ⚠️                    | ⚠️              | Partial  |
| LaTeX compile   | ✔                     | ✔               | ❌       |

This separation allows:

- reproducible inspection
- artifact-based workflows
- controlled cross-system validation
- predictable failure modes

## Stage 0 — Preflight Checks

The preflight stage validates that the execution environment satisfies the
minimum requirements required to run the Fontshow pipeline safely.

Its purpose is to detect environment-level issues early and to prevent
execution when required capabilities are missing or incompatible.

Preflight is responsible only for **environment validation** and does not
perform any form of data processing or font analysis.

---

### Documentation of stage 0

All details regarding preflight behavior, including:

- scope and responsibilities
- supported environments
- performed checks
- severity levels
- CLI and CI behavior

are documented in:

→ `docs/tools/preflight.md`

---

### Role in the pipeline of stage 0

The preflight stage acts as a **gatekeeper** for the pipeline:

- it runs before any other stage
- it may abort execution if requirements are not met
- it does not modify user data
- it does not perform font parsing or analysis

All subsequent stages assume a successful preflight execution.

## Stage 1 — System font dump

This stage is responsible for discovering fonts available on the system and
extracting raw font metadata required by downstream stages.

This stage focuses on **data collection**, not interpretation.

---

### Documentation of stage 1

All implementation details related to the system font dump, including:

- discovery mechanisms and backends
- extracted metadata fields
- charset extraction (if applicable)
- diagnostic output and logging behavior

are documented in:

→ `docs/tools/dump-fonts.md`

---

### Role in the pipeline of stage 1

The system font dump stage:

- enumerates available fonts
- extracts raw metadata
- does not perform semantic interpretation
- does not apply inventory-level validation or enrichment
- does not generate catalog artifacts

The data produced here is consumed by the inventory parsing stage.

## Stage 2 — Inventory parsing, validation and enrichment

This stage transforms raw font metadata into a structured and validated
inventory representation.

It is responsible for:

- schema validation
- normalization of extracted metadata
- semantic validation
- enforcement of strict or permissive validation modes

---

### Documentation of stage 2

All operational details for inventory parsing and validation are documented in:

→ `docs/tools/parse-inventory.md`

This includes:

- language normalization rules
- strict vs permissive validation behavior
- handling of deprecated or malformed data
- validation error semantics

---

### Role in the pipeline of stage 2

The inventory parsing stage:

- consumes raw font metadata
- produces a validated inventory representation
- applies semantic and structural checks
- does not perform font discovery
- does not generate output artifacts

All subsequent stages operate on the validated inventory produced here.

## Stage 3 — Catalog generation

The catalog generation stage transforms the validated inventory into
final output artifacts.

This stage is responsible for producing user-facing representations
based on the processed inventory data.

---

### Documentation of stage 3

All implementation details related to catalog generation, including:

- output formats
- LaTeX generation
- template handling
- error reporting and diagnostics

are documented in:

→ `docs/tools/create-catalog.md`

---

### Role in the pipeline of stage 3

The catalog generation stage:

- consumes validated inventory data
- produces final output artifacts
- does not perform validation or normalization
- does not modify inventory contents

This is the terminal stage of the Fontshow pipeline.

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
