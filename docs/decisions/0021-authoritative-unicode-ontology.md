# Decision 0021 - Authoritative Unicode Ontology

**Date**: 28/02/2026
**Status**: Accepted

## Context

Fontshow historically maintained Unicode-related knowledge through:

* handwritten script ranges
* partially duplicated Unicode tables
* runtime-derived structures
* heuristic normalization layers

This caused several issues:

* divergence from Unicode standards
* maintenance burden
* hidden inconsistencies between modules
* difficulty auditing inference correctness
* non-deterministic evolution of Unicode data

During Step 0 of the Language Inference Overhaul, the project migrated to a standards-grounded Unicode model.

## Decision

Fontshow adopts a **generated, authoritative Unicode ontology**.

All Unicode structural data is now produced from vendored standards:

* Unicode UCD:

  * Blocks.txt
  * Scripts.txt
* ISO-15924 registry

A deterministic generator:

```text
scripts/generate_unicode_tables.py
```

produces:

```text
fontshow/unicode_tables.py
```

This module is now the **single source of truth** for Unicode data.

### Architectural invariants

1. Unicode data MUST NOT be handwritten in runtime modules.
2. Runtime code MUST NOT derive Unicode structural tables.
3. All Unicode ontology changes occur via regeneration.
4. Generated files MUST NOT be manually edited.
5. unicode_tables.py represents a frozen snapshot of Unicode semantics.

### Data layers

```text
Unicode Standard
        ↓
Vendored datasets
        ↓
Generator
        ↓
unicode_tables.py   ← authoritative ontology
        ↓
Runtime inference
```

## Consequences

### Positive

* deterministic Unicode behavior
* auditability against standards
* simplified inference reasoning
* elimination of duplicated tables
* stable future refactors

### Negative

* regeneration step required when upgrading Unicode version
* generator becomes critical infrastructure

## Migration

Implemented in two commits:

* Commit 1:
  Introduced generator, ISO normalization, and dual-source bridge.

* Commit 2:
  Removed legacy tables and runtime derivations.
  unicode_tables.py became authoritative.

## Future Work

Language inference redesign (Step 1) depends on this invariant.

## Related Decisions

* ADR 0018 — Trace Logging Architecture Semantics
