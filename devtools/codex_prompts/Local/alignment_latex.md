Continue Fontshow LaTeX/ontology alignment work from the current repository state.

Ground rules:
- We are inside `.venv`.
- Follow `AGENTS.md` strictly.
- Keep changes minimal and deterministic.
- Use `apply_patch` for file edits.
- Keep docstrings NumPy-style.
- Do not move support-only alias bookkeeping into `fontshow/ontology`.

Objective:
- Evaluate and reduce the distance between the current production ontology in
  `fontshow/ontology/language_tables.py` and the scripts/languages exposed by
  the current local LaTeX installation.
- Preserve the architectural rule agreed previously:
  - production ontology contains only production-relevant canonical entries;
  - support-only alias mappings stay in maintenance scripts and reports.
- Respect the production language-normalization behavior:
  - `fontshow.inventory.semantic_validation.normalize_languages()` strips
    region/script/variant suffixes and normalizes to primary language codes;
  - Polyglossia module names already covered by that normalization path are
    support bookkeeping only, not real production-ontology distance.

Source scripts for the alignment workflow:
- `scripts/audit_local_tex_surface.py`
- `scripts/generate_tex_ontology_gap_report.py`
- `scripts/generate_tex_ontology_stubs.py`
- `scripts/generate_first_reviewed_tex_batch.py`
- `scripts/generate_tex_alignment_plan.py`

Run order, dependencies, and output meaning:
1. `python scripts/audit_local_tex_surface.py`
   - Input:
     - local `fontspec-luatex.sty`
     - local Polyglossia `gloss-*.ldf` directory
   - Output:
     - `reports/local_tex_surface.json`
   - Meaning:
     - authoritative snapshot of the current local LaTeX surface
     - lists available `fontspec` script names and Polyglossia module names
     - this is the machine-local baseline for all later comparisons

2. `python scripts/generate_tex_ontology_gap_report.py`
   - Input:
     - `reports/local_tex_surface.json`
     - production ontology in `fontshow/ontology/language_tables.py`
   - Output:
     - `reports/tex_ontology_gap_report.json`
   - Meaning:
     - compares local LaTeX support against current ontology
     - separates covered items from missing ones
     - classifies missing items as:
       - `needs_specimen`
       - `needs_alias_mapping`
       - `normalized_by_pipeline`
       - `should_not_be_language`

3. `python scripts/generate_tex_ontology_stubs.py`
   - Input:
     - `reports/tex_ontology_gap_report.json`
   - Output:
     - `reports/tex_ontology_stub_proposal.json`
   - Meaning:
     - turns the raw gap report into review-oriented buckets
     - produces:
       - `scripts`: true script stubs needing curation
       - `languages.canonical_candidates`: true canonical language gaps
       - `languages.alias_variants`: maintenance alias cases
       - `languages.pipeline_normalized`: names already normalized away by production

4. `python scripts/generate_first_reviewed_tex_batch.py`
   - Input:
     - `reports/tex_ontology_stub_proposal.json`
   - Output:
     - `reports/first_reviewed_tex_batch.json`
   - Meaning:
     - extracts only the low-risk, already-reviewed support-side mappings
     - intended for support-tooling bookkeeping, not automatic ontology promotion

5. `python scripts/generate_tex_alignment_plan.py`
   - Input:
     - `reports/tex_ontology_gap_report.json`
     - `reports/tex_ontology_stub_proposal.json`
     - `reports/first_reviewed_tex_batch.json`
   - Output:
     - `reports/tex_alignment_plan.json`
   - Meaning:
     - final staged work plan
     - gives:
       - current distance counts
       - support-only remaining work
       - true production ontology work
       - deterministic production batches of 10 items

Required workflow:
1. Regenerate the local TeX audit and gap artifacts:
   - `python scripts/audit_local_tex_surface.py`
   - `python scripts/generate_tex_ontology_gap_report.py`
   - `python scripts/generate_tex_ontology_stubs.py`
   - `python scripts/generate_first_reviewed_tex_batch.py`
   - `python scripts/generate_tex_alignment_plan.py`
2. Read the resulting reports under `reports/`.
3. Treat the alignment report as three separate buckets:
   - already covered by production ontology;
   - support-script-only work, split into:
     - alias-only items still needing maintenance-script bookkeeping;
     - names already normalized away by the production pipeline;
   - true ontology gaps requiring canonical script/language curation.
4. Execute only one low-blast-radius stage at a time:
   - first, reviewed alias/support updates if needed;
   - then true ontology additions in batches of 10 items.
5. For each batch:
   - list the exact candidate set before editing;
   - update only the necessary ontology/support files;
   - add or update deterministic tests;
   - avoid LaTeX-dependent tests.
6. After each accepted batch, run:
   - `ruff check .`
   - `mypy fontshow`
   - `pytest -q`

Current known baseline from the last audit on this machine:
- Local `fontspec` scripts: 169
- Local Polyglossia languages: 242
- Ontology-modeled `fontspec` scripts: 84
- Ontology-modeled Polyglossia languages: 13
- Missing `fontspec` scripts: 85
- Missing Polyglossia languages: 229
- Polyglossia names already normalized by the production pipeline: 121
- Remaining alias-like Polyglossia gap requiring maintenance-script mapping: 1
- Canonical language candidates: 107
- Reviewed low-risk language aliases: 40
- Reviewed low-risk script aliases: 2

Expected first inspection files:
- `reports/local_tex_surface.json`
- `reports/tex_ontology_gap_report.json`
- `reports/tex_ontology_stub_proposal.json`
- `reports/first_reviewed_tex_batch.json`
- `reports/tex_alignment_plan.json`
- `fontshow/ontology/language_tables.py`
- `tests/test_scripts_tex_ontology_audit.py`

Do not assume old generated reports are still current. Regenerate first, then
work from the regenerated reports.
