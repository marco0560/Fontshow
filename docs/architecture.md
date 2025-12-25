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

---

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

---

## Pipeline overview

The Fontshow pipeline is strictly linear:

```text
Installed fonts
      │
      ▼
dump_fonts.py
      │   (raw inventory JSON)
      ▼
parse_font_inventory.py
      │   (enriched inventory JSON)
      ▼
create_catalog.py
      │
      ▼
LaTeX catalog
```

Each stage produces a JSON-compatible structure that can be:

- inspected manually,
- cached,
- reused independently of the other stages.

---

## Data flow and contracts

The central artifact in Fontshow is the **font inventory**.

The inventory is a JSON document with two main sections:

- `metadata`: global information about the generation context
- `fonts`: a list of per-font (or per-face) descriptors

Metadata fields may include environment and tool information intended for
debugging and reproducibility purposes. Downstream stages must treat metadata
as informative and non-authoritative.


Each stage respects the following contract:

- **dump_fonts**
  Produces *raw*, low-level metadata directly extracted from font files
  and system tools.

- **parse_font_inventory**
  Adds semantic interpretation (scripts, languages, coverage inference)
  without modifying raw fields.

- **create_catalog**
  Treats the inventory as read-only input and performs rendering only.

Downstream stages must never assume the presence of optional fields unless
explicitly documented.

---

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

---

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

---

### parse_font_inventory

Responsible for:

- interpreting Unicode coverage,
- inferring scripts and languages,
- normalizing and enriching inventory entries.

It operates purely on structured data and never accesses font binaries.

---

### create_catalog

Responsible for:

- grouping fonts by family,
- selecting representative samples,
- rendering LaTeX source code.

It does not perform inference and does not alter the inventory semantics.

---

## Error handling and robustness

Fontshow adopts a best-effort error handling strategy:

- errors are captured locally whenever possible,
- partial failures are represented explicitly in the data,
- the pipeline continues unless a critical invariant is violated.

This approach ensures that:

- large font collections remain processable,
- malformed fonts do not abort the entire run,
- diagnostic information remains available for inspection.

---

## Why a procedural architecture

Fontshow intentionally avoids a class-based or object-oriented architecture.

Reasons include:

- the pipeline is naturally linear and data-driven,
- the primary abstraction is the **inventory**, not behavior,
- procedural code makes data transformations explicit and traceable,
- it aligns well with batch-style processing and reproducibility.

This choice prioritizes clarity and debuggability over extensibility through
inheritance.

---

### Inventory schema evolution

Fontshow uses a versioned JSON inventory as the central data contract
between pipeline stages.

Each inventory declares a `schema_version` in its metadata. Downstream
stages must remain tolerant to missing or unknown fields and must not
assume the presence of optional metadata.

Schema validation is intentionally *soft*: unknown schema versions or missing
fields may trigger warnings but must not abort execution. This allows older
inventories to remain usable and supports incremental schema evolution.

This design allows the inventory format to evolve without breaking
existing pipelines and supports reproducibility across different
execution environments.

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
