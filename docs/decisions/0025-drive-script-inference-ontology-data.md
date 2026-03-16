# Decision 0025 - Drive Script Inference from Ontology Data

**Date**: 16/03/2026
**Status**: Accepted

## Context

Script inference previously depended on hard-coded tables inside
`fontshow.inventory.script_analysis`. Adding support for a new writing
system required editing both ontology data and inference code.

That structure had three problems:

- the ontology already contained most of the information needed to
  describe script evidence and representative languages;
- support additions were not data-only, which made incremental
  expansion error-prone;
- special cases such as Japanese collapse, broad-neighbor scripts, and
  `unicode.max` fallbacks were not documented in the authoritative
  ontology.

The project goal for this phase is to make script support expansion
primarily a data-maintenance task: new scripts and languages should be
added by extending ontology rows, not by patching the inference engine.

## Decision

Script inference is now driven by ontology metadata stored in
`SCRIPT_INFO`, with language fallback metadata normalized in
`LANGUAGE_INFO`.

The ontology schema is extended as follows:

- `LANGUAGE_INFO` adds `primary_script`
- `SCRIPT_INFO` adds:
  - `required_blocks`
  - `optional_blocks`
  - `suppresses`
  - `inference_priority`
  - `unicode_max_ranges`
  - `block_match`
  - `collapse_group`
  - `preferred_over`

The runtime model is:

1. language rows declare their primary script explicitly;
2. script rows expose the data needed for block-based and
   `unicode.max`-based inference;
3. `script_analysis` evaluates scripts generically from ontology data;
4. collapse and precedence behavior are expressed by ontology fields
   rather than hard-coded script-name tables.

Defaults are normalized at module load time:

- `primary_script` is backfilled from the first script in each language
  profile;
- many script inference defaults are derived from the representative
  language profile;
- scripts with special disambiguation behavior override those defaults
  explicitly.

`JPAN` is introduced as a first-class ontology script so Japanese
collapse behavior is represented in production data rather than in
inference code comments or ad hoc special cases.

## Consequences

Positive:

- adding a new script now mostly means updating ontology rows;
- script inference rules live next to the script metadata they affect;
- rendering, specimen selection, and inference now share one
  authoritative script description;
- Japanese collapse and broad-neighbor precedence are explicit and
  reviewable.

Trade-offs:

- ontology rows are richer and therefore more demanding to curate;
- module-load normalization introduces a small amount of derived data
  logic in `language_tables.py`;
- preflight validation must enforce the expanded schema to keep the
  ontology trustworthy.

Operationally, the quality gates for this decision are:

- `ruff check .`
- `mypy .`
- `pytest -q`

These gates passed when this decision was adopted.
