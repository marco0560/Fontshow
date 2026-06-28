# AGENTS.md - Fontshow Repository Contract

## Mission

Work in this repository to advance the user's objectives with these priorities:

1. Correctness
2. Test integrity
3. Reproducibility
4. Traceability
5. Minimal change

Be direct. The assistant is not here to flatter the user or preserve a bad
premise. If the user's request, plan, or assumption is technically wrong,
push back clearly and explain the practical consequence.

## Operating Rules

- Treat repository files as the source of truth.
- Read before editing.
- Do not invent unseen code, missing files, or behavior.
- Keep changes small, scoped, and reversible.
- Preserve user changes in the worktree.
- Do not refactor, rename, or change APIs unless the task requires it.
- If a requested change has multiple valid implementations and the repository does not make the choice clear, ask before editing.
- If the task is impossible to complete deterministically, stop and state the blocker.

## Source Priority

Use sources in this order:

1. Repository files
2. Tests in `tests/`
3. Documentation in `docs/`
4. User instructions

Previous assistant output is not a source of truth.

## Required Tools And Skills

- If the repo provides `codira`, use `codira-workflow` before broad exploration
  or patching.
- Prefer repository-native commands through `uv run`.
- At the start of each task, inspect the skills available in the current
  session and select the minimal set that applies.
- Read the selected skill instructions before acting on them.
- Use applicable skills as active workflow rules, not as optional references.
- Use local skills when they match the task:
  - `deterministic-change-workflow` for non-trivial changes
  - `planning-refinement-gate` for ambiguous planning or architecture work
  - `numpy-docstring-enforcer` when modifying Python symbols
  - `commit-block-generator` when preparing commits
  - `roadmap-snapshots` for `issues.json` or `milestones.json`
- Use `rg` only after structured repository tools are unavailable,
  insufficient, or irrelevant to the task.

## Repository Map

| Path            | Purpose                                     |
|-----------------|---------------------------------------------|
| `src/fontshow/` | Main application code                       |
| `tests/`        | Authoritative behavioral specification      |
| `docs/`         | Architecture, contracts, and decisions      |
| `scripts/`      | Dev, release, audit, and generation tooling |
| `devtools/`     | Codex prompts and auxiliary workflows       |
| `.github/`      | CI/CD pipelines                             |
| `_archive/`     | Historical artifacts, not active code       |

### Core Code

| Area        | Path           | Responsibility                                  |
|-------------|----------------|-------------------------------------------------|
| Entry point | `__main__.py`  | CLI entry                                       |
| CLI         | `cli/`         | Command implementations                         |
| Catalog     | `catalog/`     | LaTeX document generation pipeline              |
| Common      | `common/`      | Shared domain helpers                           |
| Constants   | `constants/`   | System-wide constants and invariants            |
| Data        | `data/`        | Bundled Unicode and ISO source data             |
| Inventory   | `inventory/`   | Font metadata extraction, validation, inference |
| Platform    | `platform/`    | OS/font discovery                               |
| Preflight   | `preflight/`   | Environment validation                          |
| LaTeX       | `latex/`       | Rendering, templates, policies                  |
| Ontology    | `ontology/`    | Language/script normalization tables            |
| Schema      | `schema/`      | JSON schema definitions                         |
| Unicode     | `unicode/`     | Charset and range handling                      |
| Core        | `core/`        | Shared utilities                                |
| Diagnostics | `diagnostics/` | Warnings and reporting                          |

### CLI Entry Points

| Command              | Primary modules                                  |
|----------------------|--------------------------------------------------|
| `dump-fonts`         | `platform/`, `inventory/fonttools_extraction.py` |
| `parse-inventory`    | `inventory/`, `schema/`, `ontology/`             |
| `create-catalog`     | `catalog/`, `latex/`, `inventory/`               |
| `validate-inventory` | `inventory/schema_validation.py`, `schema/`      |
| `preflight`          | `preflight/`                                     |

Use this map to scope Codira queries. It does not replace indexed inspection.

## Tests And Documentation

- Tests define behavior.
- Prefer tests over implementation comments when behavior is unclear.
- Documentation describes intent and contracts, but tests and code win when they disagree.
- Do not weaken assertions, skip failures, or add environment-dependent tests.
- When changing public behavior, update matching tests and docs in the same change.

## Python Standards

- Use type hints.
- Prefer `Path` for filesystem paths.
- Avoid `Any` unless the boundary genuinely requires it.
- Catch only expected exceptions.
- Use NumPy-style docstrings for modified Python modules, classes, and functions.

## Architecture Constraints

Keep Fontshow pipeline boundaries intact:

| Layer     | Responsibility                                      |
|-----------|-----------------------------------------------------|
| CLI       | Arguments, orchestration, exit codes                |
| Preflight | Runtime and external-tool readiness checks          |
| Platform  | OS and Fontconfig integration                       |
| Inventory | Raw font data validation, normalization, enrichment |
| Catalog   | Catalog records, grouping, specimen selection       |
| LaTeX     | TeX escaping, templates, rendering policies         |
| Ontology  | Static language, script, Unicode reference data     |
| Core      | Shared utilities, logging, JSON, types              |

Rules:

- Keep environment-dependent behavior in `platform/`, `preflight/`, or the documented pipeline stages that explicitly require it.
- Do not make catalog rendering rediscover fonts or reinterpret raw platform state.
- Do not put user-facing argument parsing or process-exit policy in lower-level domain modules.
- Do not duplicate ontology, schema, or constant data across subsystems.

## Generated Files And Artifacts

- Do not hand-edit generated files when a generator owns them.
- Modify the generator and regenerate the artifact.
- Keep generated outputs consistent with the checked-in source of truth.

## Validation

Run the narrowest meaningful validation during development, then the declared
repository validation before closing substantial work:

```bash
uv run python scripts/validate_repo.py
```

If the primary validation cannot run, use the closest local fallback and report the reason:

```bash
ruff check .
ruff format --check .
mypy .
pytest -q
```

Do not claim checks passed unless they were run.

## Commits

When asked to commit:

- Keep the commit atomic.
- Use `commit-block-generator`.
- Use Conventional Commit format: `type(scope): summary`.
- Include root cause, fix, and validation in the body.

## TUI Interaction

- Keep status updates concise and operational.
- Ask only when a real decision or missing fact blocks deterministic progress.
- Push back on incorrect assumptions immediately.
- Prefer doing the work over narrating the workflow.
- Report changed files and validation results at the end.
