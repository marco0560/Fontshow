Implement a new `create-catalog` feature that allows selecting fonts by script and/or language.

Exact Perimeter
---------------

This section is authoritative. Do not proceed until each point is understood and respected.

1. Feature goal

   Add user-facing selection options to `fontshow create-catalog` so the rendered catalog can be restricted to fonts matching:

   - one or more scripts
   - one or more languages
   - both scripts and languages together

2. Selection sources

   Selection must use both metadata sources when present:

   - `coverage`
   - `inference`

   A font matches a requested script or language if the requested value is present in either source.

   Do not require both sources to agree.
   Do not modify upstream inference or coverage generation.

3. Combination semantics

   Default behavior when both script selectors and language selectors are present:

   - `AND`

   Meaning:

   - the font must match at least one requested script
   - and at least one requested language

   Add an explicit sub-option to switch the cross-category combination mode to:

   - `OR`

   The prompt implementation must define the CLI spelling clearly and document it.

4. Intra-category semantics

   Within each category, repeated selectors are inclusive:

   - multiple scripts mean script1 OR script2 OR ...
   - multiple languages mean lang1 OR lang2 OR ...

5. Scope of effect

   The feature must affect only the effective font set passed to catalog generation.

   It must not:

   - change inventory parsing
   - change script inference
   - change language normalization
   - change specimen selection policy
   - change LaTeX rendering policy except through the smaller selected font set

6. Existing behavior that must be preserved

   Preserve:

   - existing `--test`, `--test-font`, `--list-test-fonts`, `--number`, and `--validate-loadability` behavior
   - deterministic output ordering
   - failure behavior for missing inventories
   - quiet/verbose semantics

7. Out of scope

   Do not implement:

   - negative selection (`exclude-script`, `exclude-language`)
   - regex matching
   - fuzzy matching
   - script/language inference changes
   - schema changes
   - new inventory fields
   - LaTeX-aware language prioritization changes

Repository Grounding
--------------------

Before editing, inspect at minimum:

- `src/fontshow/cli/create_catalog.py`
- `src/fontshow/catalog/pipeline.py`
- `docs/tools/create-catalog.md`
- `tests/test_catalog_pipeline.py`
- `tests/test_create_catalog_runtime.py`
- `tests/cli/test_create-catalog.py`
- `tests/cli/test_cli_quiet_verbose.py`
- `docs/schema/language-normalization.md`
- `docs/decisions/0013-language-normalization-strategy.md`
- `docs/decisions/0016-language-normalization-validation-strategy.md`
- `docs/decisions/0025-drive-script-inference-ontology-data.md`

Implementation Requirements
---------------------------

1. Add minimal CLI surface to `create-catalog`

   Add options for:

   - selecting one or more scripts
   - selecting one or more languages
   - selecting the cross-category combination mode, defaulting to `AND`, with explicit `OR` support

   Prefer repeated options over comma-separated parsing unless the repository already establishes a different pattern.

2. Normalize comparison behavior conservatively

   For matching:

   - scripts should compare canonically and case-insensitively
   - languages should compare canonically and case-insensitively

   Reuse existing repository normalization helpers if they already exist.
   Do not invent new ontology or normalization logic if current helpers are sufficient.

3. Keep filtering localized

   The most likely implementation point is the catalog pipeline filtering stage.
   Favor a small helper in `src/fontshow/catalog/pipeline.py` rather than spreading selection logic across CLI and rendering code.

4. Define exact matching contract in code comments/docstrings

   The implementation must make these rules explicit:

   - repeated script filters are OR
   - repeated language filters are OR
   - script + language together are AND by default
   - explicit combination mode can switch to OR
   - coverage and inference are both consulted when present

5. Keep docstrings compliant

   Any modified module, function, or helper must have NumPy-style docstrings consistent with real behavior.

Testing Requirements
--------------------

Add deterministic tests without requiring LaTeX or external binaries.

At minimum, cover:

1. CLI acceptance

   Add CLI tests proving the new options are accepted by `fontshow create-catalog`.

2. Filtering semantics

   Add unit tests for the catalog pipeline covering:

   - script-only filtering
   - language-only filtering
   - default AND behavior when both categories are present
   - explicit OR behavior when both categories are present
   - repeated values within a category behave as OR
   - matching across `coverage` only
   - matching across `inference` only
   - matching when one source is missing and the other is present

3. Deterministic ordering

   Ensure filtered output remains sorted exactly as current code expects.

4. Runtime integration

   Add or extend runtime tests so `run_create_catalog()` passes the new selector state through the normal filtering flow without weakening existing invariants.

Constraints
-----------

- Minimal, surgical change set only
- No unrelated refactors
- No schema changes
- No weakening of current assertions
- No tests that require LaTeX
- No undocumented behavior changes

Validation
----------

Assume the implementation is not complete until these pass:

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

Do not include tool output or check summaries.
