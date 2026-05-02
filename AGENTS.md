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

## 5. Core Principles

- Deterministic: reproducible, verifiable outputs
- Minimal: smallest correct change
- Scoped: no unrelated modifications

Forbidden unless explicitly required:

- refactoring unrelated code
- renaming symbols
- API changes
- stylistic churn

## 6. Task Classification

A task is non-trivial if it involves:

- multiple files
- architectural decisions
- ambiguity
- potential behavioral impact

## 7. Execution Workflow (MANDATORY)

For non-trivial tasks use `deterministic-change-workflow`

1. Analyze request
2. Identify gaps → STOP if needed
3. Propose plan
4. WAIT for approval
5. Execute
6. Validate

Do not skip steps.

If planning is ambiguous → use `planning-refinement-gate`.

## 8. Codira Exploration (MANDATORY)

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

## 9. Skills Usage

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

## 10. Change Strategy

- Prefer small, atomic changes
- One subsystem at a time
- Separate refactor / feature / fix

## 11. Validation Contract

All checks MUST pass.

Primary:

```bash
pre-commit run --all-files
pytest -q
```

Fallback:

```bash
black --check .
ruff check .
mypy .
pytest -q
```

Rules:

- fix all failures
- do not weaken tests
- do not ignore errors

## 12. Test Contract

Tests define behavior.

Requirements:

- deterministic
- environment-independent

Forbidden:

- weakening assertions
- introducing flakiness
- bypassing failures

If tests contradict assumptions → tests win.

## 13. Strict Patch Discipline

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

## 14. Architecture Constraints

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

## 15. Build & Artifacts

- do not edit generated files
- modify generators instead
- keep build outputs consistent

## 16. Coding Standards

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

## 17. Error Handling

- fail fast
- catch only expected exceptions
- avoid broad `except Exception`

## 18. Regression Policy

Bugs include:

- platform breakage
- performance regressions
- CLI/output changes
- optional feature regressions

## 19. Debugging Discipline

- reproduce first
- identify root cause
- avoid speculative fixes

## 20. Commit Contract

Use `commit-block-generator`

- single atomic commit
- format: `type(scope): summary`

Body must include:

- root cause
- fix
- validation

Do NOT include toolchain status lines.

## 21. Roadmap Snapshots

Use `roadmap-snapshots` for:

- issues.json
- milestones.json

Rules:

- treat as local artifacts
- verify schema and completeness
- do not infer missing fields

## 22. Anti-Patterns (Forbidden)

- guessing code
- blind scanning
- duplicating logic
- silent failures
- skipping validation

## 23. Session Stability

Monitor:

- context drift
- assumption creep

If detected:

→ STOP
→ Recommend reset

## 24. Heuristics

- small changes can have wide effects
- complex code encodes edge cases
- correctness > elegance

## 25. Default Interaction Mode

- minimal prose
- command-oriented
- no verbosity unless requested

## 26. Meta Rule

Do not reference this contract in responses.
Do not explain compliance.
Only execute.

## 27. When in Doubt

STOP and ask.
