# AGENTS.md — Fontshow Repository Contract

## 0. Mission

You are operating on the Fontshow repository.

Priority:

1. Correctness
2. Test integrity
3. Reproducibility
4. Traceability
5. Minimality of change

Fluency is irrelevant.

## 1. Operating Mode

Mode: HARD-FAIL DETERMINISTIC

Rules:

- Never guess
- Never infer missing code
- Never reconstruct unseen files
- Never approximate behavior

If required information is missing:

-> STOP
-> Ask for clarification

## 2. Sources of Truth

Priority order:

1. Repository files
2. Tests (`tests/`) as the authoritative behavior contract
3. Project documentation (`docs/`)
4. User instructions

Previous assistant output is not a source of truth.

## 3. Repository-Specific Constraints

- Fontshow is a deterministic, test-driven engineering project.
- Scope control is strict: do only what is requested.
- Do not refactor unrelated code, rename symbols, introduce stylistic churn, or modify APIs unless explicitly required.
- Stop immediately if requirements are ambiguous, file context is missing, expected behavior is unclear, or a change risks breaking the CLI contract.

## 4. Required Shared Skills

Use the following shared skills for the corresponding task classes:

- `deterministic-change-workflow` for non-trivial code changes, bug fixes, and feature work
- `numpy-docstring-enforcer` whenever modifying modules, classes, public functions, or private functions
- `codira-workflow` before broad code exploration or patching
- `commit-block-generator` when committing changes or proposing the final commit block

If a required skill is unavailable, state that explicitly and apply the same rules manually.

## 5. Validation Contract

Assume the following commands are the required validation surface:

```bash
pre-commit run --all-files
pytest -q
```

`pre-commit` includes and replaces formatter, lint, and type-check gates managed by repository configuration.

All required checks must pass before concluding.

## 6. Test Constraints

GitHub CI does not guarantee LaTeX availability.

Tests must:

- be deterministic
- be environment-independent
- not require LaTeX installation
- not rely on unmocked external binaries

Never weaken assertions or introduce flaky behavior.

## 7. Repository Awareness

Primary subsystems:

- CLI: `src/fontshow/cli/`
- Inventory: `src/fontshow/inventory/`
- Catalog: `src/fontshow/catalog/`
- Preflight: `src/fontshow/preflight/`
- Ontology: `src/fontshow/ontology/`

For non-trivial work, consult these planning artifacts when relevant:

- `issues.json`
- `milestones_plan.json`

Do not invent or reinterpret issue or milestone intent.

## 8. Commit Contract

Commit messages must satisfy `.githooks/commit-msg.py`.

Allowed types:

- `feat`
- `fix`
- `docs`
- `perf`
- `refactor`
- `test`
- `chore`
- `style`

Allowed scopes:

- `build`
- `catalog`
- `ci`
- `cli`
- `config`
- `core`
- `decision`
- `dev`
- `diagnostics`
- `discovery`
- `docs`
- `dump`
- `git`
- `inventory`
- `latex`
- `output`
- `ontology`
- `parser`
- `planning`
- `platform`
- `release`
- `schema`
- `unicode`
- `validation`

The first line must match `type(scope): summary`, with an optional scope and a summary length of 1 to 72 characters.

## 9. Session Stability

Monitor for context drift, assumption creep, and loss of file grounding.

If detected:

-> recommend RESET
