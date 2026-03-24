Implement a new `create-catalog` feature that renders multiple specimens per selected font family based on all scripts and/or all languages already present in inventory metadata.

Exact Perimeter
---------------

This section is authoritative. Do not proceed until every point is understood and respected.

1. Feature goal

   Add user-facing `create-catalog` flags that can print additional specimen lines derived from:

   - all scripts currently present in the selected font metadata
   - all languages currently present in the selected font metadata

   These are separate flags.

2. Metadata sources

   The feature must inspect both metadata sources when present:

   - `coverage`
   - `inference`

   The effective script set for a font is the union of scripts found in those sources.
   The effective language set for a font is the union of languages found in those sources.

   Do not require the two sources to agree.
   Do not modify how either source is produced.

3. Interaction with existing filtering

   The feature applies only to fonts already selected by the normal `create-catalog` flow and any other active flags.

   This means the font set is determined first by existing filters such as:

   - test-family filtering
   - count limiting
   - script/language selection filters if they exist
   - loadability filtering if enabled

   Only after that selection is complete may multiple specimens be derived for rendering.

4. Separate flags

   Add two independent feature flags:

   - one that enables rendering specimens for all scripts
   - one that enables rendering specimens for all languages

   If both flags are enabled, both sets must be rendered.

5. Source of rendered specimens

   Additional specimens are a render-time concern only.

   They must be derived from the ontology / existing specimen-selection helpers when possible.

   If a requested script or language is present in metadata but no curated specimen mapping can be resolved, fall back to the font's canonical inventory specimen:

   - `specimen_text`

6. Default target variant

   By default, the multi-specimen output for a family must be rendered only for:

   - the variant whose style/subfamily is `Regular`, if present
   - otherwise the first family variant in existing deterministic order

7. Per-variant sub-flag

   Add an explicit sub-flag that switches the feature from representative-variant mode to:

   - render the multi-specimen output for each variant in the family

   The prompt implementation must define the exact CLI spelling clearly.

8. Cardinality

   "ALL" is literal and unbounded.

   Do not introduce:

   - hard caps
   - soft caps
   - top-N truncation
   - prioritization-based omission

9. Scope of change

   This feature must remain in the renderer / catalog-generation layer.

   It must not:

   - change inventory schema
   - persist multiple specimens to JSON
   - change `parse-inventory`
   - change script inference
   - change language normalization
   - change upstream specimen generation semantics

10. Existing behavior that must be preserved

    Preserve:

    - canonical `specimen_text` semantics in inventory
    - current single-specimen behavior when the new flags are absent
    - deterministic output ordering
    - existing family grouping behavior
    - existing CLI failure and verbosity behavior

11. Out of scope

    Do not implement:

    - schema changes
    - additional persisted fields
    - negative selection
    - heuristics that guess dominant script/language
    - any cap on rendered specimens
    - refactors unrelated to multi-specimen rendering

Planning Alignment
------------------

This feature aligns with the tracked repository issue:

- issue `#60` `Multi-specimen rendering`

Stay aligned with that issue's architectural intent:

- renderer-layer enhancement
- no schema change
- canonical specimen remains canonical

Repository Grounding
--------------------

Before editing, inspect at minimum:

- `src/fontshow/cli/create_catalog.py`
- `src/fontshow/catalog/document.py`
- `src/fontshow/catalog/pipeline.py`
- `src/fontshow/latex/policy.py`
- `src/fontshow/inventory/specimens.py`
- `src/fontshow/common/specimens.py`
- `src/fontshow/catalog/labels.py`
- `src/fontshow/ontology/language_tables.py`
- `docs/tools/create-catalog.md`
- `tests/test_catalog_document.py`
- `tests/test_create_catalog_runtime.py`
- `tests/cli/test_create-catalog.py`
- `tests/cli/test_cli_quiet_verbose.py`
- `issues.json` issue `#60`

Implementation Requirements
---------------------------

1. Add minimal CLI surface

   Add separate flags to `create-catalog` for:

   - render all script-based specimens
   - render all language-based specimens

   Add one explicit sub-flag controlling target variant scope:

   - representative variant only
   - each variant

   Keep the default aligned with the perimeter above.

2. Keep specimen derivation in the render path

   Derive additional specimens only during catalog rendering.

   Do not write them back into inventory structures on disk.
   Do not change the meaning of `specimen_text`.

3. Define deterministic ordering explicitly

   The implementation must choose and document deterministic ordering for:

   - the effective script list per font
   - the effective language list per font
   - the combined rendered output when both flags are enabled

   Prefer stable normalized ordering and avoid dependence on dictionary iteration order.

4. Representative-variant selection

   Implement a small deterministic helper that selects:

   - a `Regular` style/subfamily variant when present
   - otherwise the first variant in current family order

   Use this only when the per-variant sub-flag is not enabled.

5. Fallback behavior

   When a script/language specimen cannot be resolved from curated data:

   - use the font's canonical `specimen_text`

   This fallback must be deterministic and must not crash rendering.

6. Rendering output design

   The implementation must keep output readable and deterministic.
   It may introduce repeated specimen blocks or labeled sub-blocks under a family entry, but it must not alter unrelated rendering policy.

7. Docstring compliance

   Any modified module, function, or helper must keep NumPy-style docstrings consistent with actual behavior.

Testing Requirements
--------------------

Add deterministic tests without requiring LaTeX or external binaries.

At minimum, cover:

1. CLI acceptance

   Add CLI tests proving the new flags are accepted by `fontshow create-catalog`.

2. Default off behavior

   Verify that without the new flags the existing single-specimen rendering behavior is unchanged.

3. Representative-variant behavior

   Add document-level tests proving:

   - `Regular` is preferred when present
   - first variant is used when `Regular` is absent

4. Per-variant mode

   Add tests proving the explicit sub-flag renders multi-specimen output for each family variant.

5. Metadata union semantics

   Add tests proving scripts and languages are collected from:

   - `coverage` only
   - `inference` only
   - both sources together

6. Fallback semantics

   Add tests proving unresolved script/language specimen lookup falls back to canonical `specimen_text`.

7. Output determinism

   Add tests pinning deterministic order of rendered multi-specimen blocks.

Constraints
-----------

- Minimal, surgical change set only
- No schema changes
- No changes to upstream parse/inference behavior
- No weakening of existing assertions
- No tests that require LaTeX
- No unbounded nondeterminism despite unbounded specimen count

Validation
----------

Assume the implementation is incomplete until these pass:

```bash
pre-commit run --all-files
pytest -q
```

Commit Block
------------

After implementation, propose a single atomic commit block that is 15-20 lines long and compliant with `.githooks/commit-msg.py`.

Use:

- an allowed conventional-commit type
- an allowed scope
- `Refs: #60`

Do not include tool output or check summaries.
