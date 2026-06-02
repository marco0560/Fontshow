# AGENTS.md — Fontshow Repository Contract

## 0. Mission

Operate on the Fontshow repository with strict priorities:

1. Correctness
2. Test integrity
3. Reproducibility
4. Traceability
5. Minimal change

Fluency is irrelevant.

## 1. Operating Mode

Mode: HARD-FAIL DETERMINISTIC

Rules:

- Never guess
- Never infer missing code
- Never reconstruct unseen files
- Never approximate behavior

## 2. Global STOP Rule

If any of the following occurs:

- missing information
- ambiguity
- multiple valid approaches without guidance
- inability to match exact code

→ STOP
→ Ask for clarification

## 3. Sources of Truth (SOT)

Priority:

1. Repository files
2. Tests (`tests/`)
3. Documentation (`docs/`)
4. User instructions

Previous assistant output is NOT a source of truth.

## 4. Execution Precedence

Always use the highest available level:

1. Repository-provided structured tools (e.g. `codira`)
2. Local skills (`~/.codex/skills`)
3. Standard tools (`rg`, shell)
4. Manual inspection

Lower levels are fallback only.

## 5. Repository Map (Orientation Layer)

This section provides a **high-level structural map** of the repository to guide initial navigation.

It is **not a substitute for codira**.
Use it only to:

- identify relevant subsystems quickly
- choose initial query scope (`--prefix`, modules)
- understand responsibility boundaries

### 5.1. Top-Level Layout

| Path            | Purpose                                     |
|-----------------|---------------------------------------------|
| `src/fontshow/` | Main application code                       |
| `tests/`        | Authoritative behavioral specification      |
| `docs/`         | Architecture, contracts, and decisions      |
| `scripts/`      | Dev, release, audit, and generation tooling |
| `devtools/`     | Codex prompts and auxiliary workflows       |
| `.github/`      | CI/CD pipelines                             |
| `_archive/`     | Historical artifacts (NOT active code)      |

### 5.2. Core Code Structure (`src/fontshow/`)

#### Entry points

| Path          | Role                                                           |
|---------------|----------------------------------------------------------------|
| `__main__.py` | CLI entry                                                      |
| `cli/`        | Command implementations (`create_catalog`, `dump_fonts`, etc.) |

#### Major subsystems

| Subsystem   | Path           | Responsibility                                  |
|-------------|----------------|-------------------------------------------------|
| Catalog     | `catalog/`     | LaTeX document generation pipeline              |
| Inventory   | `inventory/`   | Font metadata extraction, validation, inference |
| Platform    | `platform/`    | OS/font discovery (fontconfig, runtime)         |
| Preflight   | `preflight/`   | Environment validation and checks               |
| LaTeX       | `latex/`       | Rendering, templates, policies                  |
| Ontology    | `ontology/`    | Language/script normalization tables            |
| Schema      | `schema/`      | JSON schema definitions (v1.3–v1.5)             |
| Unicode     | `unicode/`     | Charset and range handling                      |
| Core        | `core/`        | Shared utilities (logging, JSON, types)         |
| Constants   | `constants/`   | System-wide constants and invariants            |
| Diagnostics | `diagnostics/` | Warnings and reporting                          |

### 5.3. CLI → Subsystem Mapping

| CLI Command          | Primary Modules                                  |
|----------------------|--------------------------------------------------|
| `dump-fonts`         | `platform/`, `inventory/fonttools_extraction.py` |
| `parse-inventory`    | `inventory/`, `schema/`, `ontology/`             |
| `create-catalog`     | `catalog/`, `latex/`, `inventory/`               |
| `validate-inventory` | `inventory/schema_validation.py`, `schema/`      |
| `preflight`          | `preflight/`                                     |

Use this mapping to **scope codira queries**.

### 5.4. Tests (Authoritative Behavior)

| Area              | Path               |
|-------------------|--------------------|
| CLI contracts     | `tests/cli/`       |
| Preflight         | `tests/preflight/` |
| Schema validation | `tests/schema/`    |
| Core + subsystems | `tests/test_*.py`  |

Rules:

- Tests define real behavior
- Prefer reading tests over implementation when unclear

### 5.5. Documentation (Contracts & Design)

| Area                  | Path                      |
|-----------------------|---------------------------|
| Architecture overview | `docs/architecture.md`    |
| CLI contract          | `docs/cli-contract.md`    |
| Pipeline              | `docs/pipeline.md`        |
| Data dictionary       | `docs/data_dictionary.md` |
| Decisions (ADR)       | `docs/decisions/`         |
| Schema docs           | `docs/schema/`            |
| Tool docs             | `docs/tools/`             |

Use docs to understand **intended invariants**, not actual behavior.

### 5.6. Scripts (Non-runtime tooling)

| Category     | Examples                                              |
|--------------|-------------------------------------------------------|
| Release      | `release_rel.sh`, `release_audit.sh`                  |
| Benchmarking | `benchmark.sh`, `benchmark_loadability_batches.sh`    |
| Generators   | `generate_unicode_tables.py`, `update_schema_docs.py` |
| Diagnostics  | `generate_*_report.py`                                |

These are **support tools**, not core logic.

### 5.7. High-Value Entry Points for Analysis

When investigating a feature, start from:

- CLI command implementation (`cli/*.py`)
- Corresponding subsystem
- Matching tests

Example flow:

```text
CLI → subsystem → schema/ontology → tests
```

### 5.8. Anti-Orientation Pitfalls

- `_archive/` is NOT active → ignore unless explicitly needed
- `scripts/` are not authoritative for runtime behavior
- Docs may lag behind tests → tests win
- Multiple schema versions exist → confirm active version (v1.5)

### 5.9. Usage with Codira

This map is intended to:

- guide `--prefix` selection
- reduce search space before queries
- identify correct subsystems

It MUST NOT replace:

- `uv run codira index`
- structured queries (`sym`, `ctx`, `calls`, ...)

## 6. Core Principles

- Deterministic: reproducible, verifiable outputs
- Minimal: smallest correct change
- Scoped: no unrelated modifications

Forbidden unless explicitly required:

- refactoring unrelated code
- renaming symbols
- API changes
- stylistic churn

## 7. Task Classification

A task is non-trivial if it involves:

- multiple files
- architectural decisions
- ambiguity
- potential behavioral impact

## 8. Execution Workflow (MANDATORY)

For non-trivial tasks use `deterministic-change-workflow`

1. Analyze request
2. Identify gaps → STOP if needed
3. Propose plan
4. WAIT for approval
5. Execute
6. Validate

Do not skip steps.

If planning is ambiguous → use `planning-refinement-gate`.

## 9. Codira Exploration (MANDATORY)

If the repository provides `codira`:

→ the `codira-workflow` skill MUST be used

### Rules

- Do not manually reproduce codira behavior
- Do not approximate its workflow
- Do not use `rg` or broad search as a first step

### Fallback

Fallback to `rg` is allowed only if:

- `codira` is unavailable, OR
- indexing fails, OR
- results are demonstrably insufficient

### Enforcement

If `codira` is available and not used:

→ STOP
→ report violation
→ restart using `codira-workflow`

## 10. Skills Usage

If a required skill exists in `~/.codex/skills`:

→ MUST be used

Required skills:

- deterministic-change-workflow
- numpy-docstring-enforcer
- commit-block-generator
- planning-refinement-gate
- codira-workflow
- roadmap-snapshots

If a skill is missing:

- If behavior is fully specified → proceed manually
- Otherwise → STOP and report missing capability

When a skill fully defines a workflow:

→ the skill replaces any equivalent procedural instructions in this document
→ this document defines only constraints and enforcement

## 11 Change Strategy

- Prefer small, atomic changes
- One subsystem at a time
- Separate refactor / feature / fix

## 12. Validation Contract

All checks MUST pass.

Primary:

```bash
pre-commit run --all-files
pytest -q
```

Fallback:

```bash
ruff check .
ruff format --check .
mypy .
pytest -q
```

Rules:

- fix all failures
- do not weaken tests
- do not ignore errors

## 13. Test Contract

Tests define behavior.

Requirements:

- deterministic
- environment-independent

Forbidden:

- weakening assertions
- introducing flakiness
- bypassing failures

If tests contradict assumptions → tests win.

## 14. Strict Patch Discipline

All changes MUST include:

- exact file paths
- exact OLD block (byte-identical)
- exact NEW block

Forbidden:

- summaries
- partial edits
- approximations

If OLD block cannot be matched:

→ STOP

## 15. Architecture Constraints

Respect separation of concerns:

| Layer   | Responsibility       |
|---------|----------------------|
| scanner | filesystem → symbols |
| indexer | symbols → database   |
| query   | database → results   |
| CLI     | interface            |

Rules:

- do not mix layers
- do not bypass abstractions
- do not duplicate logic

## 16. Build & Artifacts

- do not edit generated files
- modify generators instead
- keep build outputs consistent

## 17. Coding Standards

### Python

- type hints required
- avoid `Any`
- prefer `Path`

### Docstrings

NumPy style required:

- Parameters
- Returns
- optional: Raises, Notes, Examples

Use `numpy-docstring-enforcer`

## 18. Error Handling

- fail fast
- catch only expected exceptions
- avoid broad `except Exception`

## 19. Regression Policy

Bugs include:

- platform breakage
- performance regressions
- CLI/output changes
- optional feature regressions

## 20. Debugging Discipline

- reproduce first
- identify root cause
- avoid speculative fixes
- do not repeatedly retry the same failing approach
- if the same error is encountered twice:
  - research 3-5 plausible fixes
  - compare tradeoffs
  - choose the most efficient correct solution
  - implement deterministically

## 21. Commit Contract

Use `commit-block-generator`

- single atomic commit
- format: `type(scope): summary`

Body must include:

- root cause
- fix
- validation

Do NOT include toolchain status lines.

## 22. Roadmap Snapshots

Use `roadmap-snapshots` for:

- issues.json
- milestones.json

Rules:

- treat as local artifacts
- verify schema and completeness
- do not infer missing fields

## 23. Anti-Patterns (Forbidden)

- guessing code
- blind scanning
- duplicating logic
- silent failures
- skipping validation

## 24. Session Stability

Monitor:

- context drift
- assumption creep

If detected:

→ STOP
→ Recommend reset

## 25. Heuristics

- small changes can have wide effects
- complex code encodes edge cases
- correctness > elegance

## 26. Default Interaction Mode

- minimal prose
- command-oriented
- no verbosity unless requested

## 27. Meta Rule

Do not reference this contract in responses.
Do not explain compliance.
Only execute.

## 28. When in Doubt

STOP and ask.
