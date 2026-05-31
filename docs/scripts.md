# Development Scripts

This document describes the scripts currently present in the repository
`scripts/` directory and the status of each one.

Scripts in this directory are developer tooling, maintenance helpers, or
local audit utilities. They are not part of the public Fontshow runtime API.

The inventory below distinguishes between:

- actively wired scripts used by hooks or bootstrap-installed aliases
- maintained manual helpers
- niche or local-only scripts
- retired scripts kept only in Git history

---

## Hook- and Alias-Managed Scripts

These scripts are part of the repository's current operational workflow.

### bootstrap_dev_environment.py

Fresh-clone bootstrap entrypoint.

Responsibilities:

- create `.venv`
- upgrade `pip`, `setuptools`, and `wheel`
- install `fontshow` in editable mode with `.[dev]`
- apply repo-local Git configuration and sanctioned aliases
- run `pre-commit run --all-files` and `pytest -q` by default

Status:

- recommended contributor entrypoint
- documented in `README.md`, `docs/getting_started.md`, and `docs/CONTRIBUTING.md`
- covered by `tests/test_bootstrap_dev_environment.py`

### clean_repo.py

Repository cleanup helper.

Responsibilities:

- remove ignored/generated artifacts
- preserve protected paths such as `.venv`
- support `--dry-run`

Status:

- installed as `git clean-artifacts` by the bootstrap script
- documented in `README.md` and `docs/testing.md`
- retained as the single supported cleanup utility

### generate_cheatsheet.py

Generated documentation helper for `docs/cheatsheet.md`.

Status:

- called by pre-commit
- documented in `docs/CONTRIBUTING.md`
- not part of normal runtime usage

### update_schema_docs.py

Synchronize `docs/schema/inventory_v*.md` with the committed JSON schema.

Status:

- called by pre-commit
- not part of runtime usage
- authoritative source remains the schema JSON under `src/fontshow/schema/`

### generate_bash_completion.py

Generate the checked-in Bash completion artifact:

```bash
scripts/completions/fontshow.bash
```

Status:

- maintained developer helper
- documented in `docs/bash-completion.md`
- indirectly covered by `tests/test_bash_completion.py`

### new_decision.py

Create a new decision record under `docs/decisions/`.

Status:

- installed as `git new-decision` by the bootstrap script
- maintained documentation helper
- interactive by design

### release_preview.py

Run a local `semantic-release --dry-run` preview.

Status:

- installed as `git release-preview` by the bootstrap script
- documented in `docs/CONTRIBUTING.md`
- requires local Node / `npx` / `semantic-release` availability
- uses `.releaserc.json` by default

### generate_github_snapshot.py

Generate paginated local GitHub planning snapshots:

- `issues.json`
- `milestones.json`

Status:

- installed as `git gen-issues` and `git gen-miles` by the bootstrap script
- uses the GitHub CLI GraphQL API
- paginates top-level issue and milestone connections
- paginates nested milestone issue connections
- covered by `tests/test_generate_github_snapshot.py`

### release_audit.sh

Release-safety audit executed before guarded release pushes and by the
pre-push hook.

Status:

- called by `.githooks/pre-push`
- installed as `git release-audit` by the bootstrap script
- documented in `docs/engineering/release-system.md`

### release_rel.sh

Guarded release wrapper used by `git rel`.

Status:

- installed as `git rel` by the bootstrap script
- documented in `docs/engineering/release-system.md`

### release_system_selfcheck.sh

Validate the local release-system setup.

Status:

- installed as `git release-check` by the bootstrap script
- documented in `docs/engineering/release-system.md`

### generate_bootstrap_audit_report.py

Generate `bootstrap_audit_report.txt`, a deterministic repository audit
snapshot used for audit-oriented workflows.

Status:

- installed as `git gen-boot-report` by the bootstrap script
- niche but retained
- not required for normal development

### verify_bootstrap_audit_report.py

Verify the current repository state against `bootstrap_audit_report.txt`.

Status:

- installed as `git ver-boot-report` by the bootstrap script
- niche but retained
- not required for normal development

---

## Maintained Manual Helpers

These scripts are current and useful, but are not called automatically by
hooks and are not essential for a normal contributor workflow.

### generate_unicode_tables.py

Regenerate committed Unicode-derived Python tables from vendored Unicode data.

Status:

- documented in `src/fontshow/data/unicode/README.md`
- partially covered by `tests/test_scripts_generate_unicode_tables.py`
- relevant only when vendored Unicode inputs change

### check_actions_runtime.py

Inspect repository GitHub Actions workflows for likely Node runtime drift.

Status:

- manual maintenance helper for workflow upkeep
- useful when GitHub Actions deprecates a Node runtime
- not currently wired into hooks or contributor bootstrap

### setup_benchmark_fonts.sh

Generate ignored benchmark font fixtures under `tests/fixtures/fonts_dir/`.

Status:

- manual performance helper
- documented in `docs/performance.md`
- downloads pinned OFL-compatible Google Fonts files
- idempotent for the selected `light`, `medium`, or `heavy` profile

### benchmark.sh

Run on-demand Hyperfine benchmarks for `dump-fonts`, `parse-inventory`,
and `create-catalog`.

Status:

- manual performance helper
- documented in `docs/performance.md`
- requires the repository `.venv`
- requires `hyperfine` on `PATH`
- writes ignored JSON results under `tests/fixtures/benchmark_results/`

### benchmark_loadability_batches.sh

Run on-demand Hyperfine benchmarks for serial and bounded parallel
LuaLaTeX loadability batch probing.

Status:

- manual performance helper
- documented in `docs/performance.md`
- requires the repository `.venv`
- requires `hyperfine` and `lualatex` on `PATH`
- writes ignored JSON results under `tests/fixtures/benchmark_results/`

### run_loadability_probe.py

Replay LuaLaTeX loadability probing from a prepared inventory with a
selected batch size and job count.

Status:

- internal helper for `benchmark_loadability_batches.sh`
- not part of the user-facing `fontshow` CLI
- preserves serial production defaults unless called explicitly

---

## TeX / Ontology Maintenance Helpers

These scripts support staged maintenance of the TeX-facing ontology and local
TeX capability audits. They are intentionally manual and local-only.

### audit_local_tex_surface.py

Audit locally installed `fontspec` and Polyglossia support into a deterministic
JSON report.

### generate_tex_ontology_gap_report.py

Compare the local TeX audit report against the committed ontology and classify
gaps.

### generate_tex_ontology_stubs.py

Convert the gap report into review-oriented ontology stub proposals.

### generate_first_reviewed_tex_batch.py

Select a conservative first batch of low-risk TeX / ontology follow-up work.

### generate_tex_alignment_plan.py

Combine the TeX audit outputs into a staged alignment plan.

Status for the whole group:

- deterministic local maintenance helpers
- covered by `tests/test_scripts_tex_ontology_audit.py`
- not required for ordinary development

---

## Retired Scripts

### clean_repo.ps1

Retired.

Reason:

- duplicated the behavior of `clean_repo.py`
- was not called by hooks
- was not installed by the repository bootstrap alias set
- was not documented as part of the active contributor workflow
- conflicted with the repository's Python-first tooling direction

Recovery:

- the file remains available in Git history if needed for archaeology or
  recovery

### test_fontshow_gentoo.py

Retired.

Reason:

- it had never been exercised as part of the maintained repository workflow
- it had already drifted from the current CLI contract
- if a platform-specific end-to-end helper is needed again, it is safer to
  rewrite it from current requirements than to preserve an untrusted legacy
  script

Recovery:

- the file remains available in Git history if needed for archaeology or
  recovery

### docstring_audit_extractor.py

Retired.

Reason:

- `repoindex audit-docstrings` is now the authoritative repository-wide
  docstring audit tool
- keeping a second local audit script created conflicting results and a weaker
  maintenance path
- targeted filtering should be done by piping `repoindex audit-docstrings`
  output through `rg`, not by relying on a parallel audit implementation

Replacement:

```bash
repoindex audit-docstrings
repoindex audit-docstrings | rg 'git_alias_entries|build_bootstrap_commands'
```

Recovery:

- the file remains available in Git history if needed for archaeology or
  recovery

---

## Release Guard Helpers

These shell helpers remain active because they are part of the current release
system described in `docs/engineering/release-system.md`.

### changelog_guard.sh

Validate `CHANGELOG.md` structure and top-version consistency.

### tag_guard.sh

Validate tag ancestry and release-history invariants.

Status:

- active release-system helpers
- invoked indirectly by the documented release workflow
- retained despite Decision 0007 because they are existing operational release
  guards, not new helper scripts
