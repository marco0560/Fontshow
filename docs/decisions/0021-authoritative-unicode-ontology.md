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
src/fontshow/ontology/unicode_tables.py
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

### Script-Gated Language Inference (Follow-up Rule)

Language inference operates under a script-authoritative model.

Language inference no longer derives languages from Unicode blocks.
Scripts are mandatory evidence.

When charset-derived script inference produces a non-empty set of scripts,
candidate languages MUST be restricted to languages whose primary script
belongs to the inferred script set.

Formally:

```text
LANGUAGE_PRIMARY_SCRIPT(language) ∈ inferred_scripts
```

This rule applies only to charset-derived inference.

Symbolic fonts (emoji, icon, or symbol fonts) may produce no inferred
scripts; in this case the script gate is intentionally disabled and
legacy permissive behavior is retained.

Canonical Latin fallback is now defined in terms of inferred scripts
(LATN-only) rather than Unicode block presence.

Future inference sources (e.g., name-based heuristics) may adopt the
same constraint but require separate evaluation.
