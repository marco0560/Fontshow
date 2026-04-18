# AGENTS.md — Fontshow Repository Contract

## 0. Mission

You are operating on the Fontshow repository.

Priority order:

1. Correctness
2. Test integrity (authoritative behavior)
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

→ STOP
→ Ask for clarification

## 2. Sources of Truth (SOT)

Priority order:

1. Repository files (filesystem)
2. Tests (`tests/`) → authoritative behavior contract
3. Project documentation (`docs/`)
4. User instructions

Previous assistant output is NOT a source of truth.

If something is not visible → STOP.

## 3. Core Principles

### 3.1 Determinism

All outputs must be:

- reproducible
- verifiable
- minimal

No “best effort”.

### 3.2 Minimalism (LEAN)

- Prefer the smallest correct solution
- Avoid premature abstraction
- Do not introduce frameworks or patterns unless required

### 3.3 Scope Control

Strictly limit changes to the requested task.

Forbidden unless explicitly required:

- Refactoring unrelated code
- Renaming symbols
- API changes
- Stylistic churn

If a change risks unintended impact:

→ STOP
→ Ask for clarification

## 4. Execution Workflow (MANDATORY)

For any non-trivial task:

1. Analyze request
2. Identify missing information
3. Ask clarification questions if needed
4. Propose a concrete plan
5. WAIT for approval
6. Execute the plan
7. Validate (Section 7)
8. Ensure behavioral correctness (tests)
9. Produce commit block (if applicable)

Do NOT skip steps.

## 5. Deterministic Exploration

Before modifying code:

1. Verify symbols:

    ```bash
    rg <query>
    ```

2. If available, use repository tools (e.g. context/index tools)

3. Read actual source files before editing

Never modify code based only on assumptions.

## 6. Strict Patch Discipline

All code changes MUST be provided as:

- explicit file paths
- exact OLD block (byte-identical)
- exact NEW block

Rules:

- No summaries
- No partial edits
- No reconstructed context
- No “approximate matches”

If OLD block cannot be matched exactly → STOP.

## 7. Validation Contract

All required checks MUST pass before concluding.

Preferred:

```bash
pre-commit run --all-files
pytest -q
```

If `pre-commit` is not available, run equivalent toolchain:

```bash
black --check .
ruff check .
mypy .
pytest -q
```

Rules:

- Fix all failures BEFORE concluding
- Do not ignore warnings/errors
- Do not weaken tests to pass validation

## 8. Test Contract

Tests are the authoritative behavioral specification.

Requirements:

- Deterministic
- Environment-independent
- No reliance on external systems unless explicitly allowed

Forbidden:

- Weakening assertions
- Introducing flakiness
- Bypassing failing tests

If tests contradict assumptions → tests win.

## 9. Environment Constraints

Assume execution inside project-local environment:

- `.venv` MUST be used when present

Use one of:

```bash
source .venv/bin/activate
```

or explicit paths:

```bash
.venv/bin/<tool>
```

Never rely on global/system Python or tools.

## 10. Repository Awareness

Understand repository structure before changes.

Typical subsystems may include:

- CLI
- Core logic
- Data/processing layers
- Validation/preflight
- Output/rendering

Consult when relevant:

- `issues.json`
- `milestones_plan.json`
- other planning artifacts

Do NOT reinterpret issue intent.

## 11. Architecture Constraints

Respect separation of concerns.

Example pattern:

| Layer      | Responsibility       |
|------------|----------------------|
| scanner    | filesystem → symbols |
| indexer    | symbols → database   |
| query      | database → results   |
| CLI        | user interface       |

Rules:

- Do not mix layers
- Do not bypass abstractions
- Do not duplicate existing logic

## 12. Coding Standards

### Python

- Type hints required
- Avoid `Any` unless justified
- Prefer `Path` over string paths

### Docstrings

Use NumPy style.

Required for:

- modules
- classes
- non-trivial functions

Must include:

- Parameters
- Returns

Include when applicable:

- Raises
- Notes
- Examples

Docstrings must reflect actual behavior (no drift).

## 13. Error Handling

- Fail fast
- Catch only expected exceptions
- Avoid broad `except Exception`

## 14. Commit Contract

If committing or proposing a commit:

- Use `commit-block-generator` if available
- Produce a **single atomic commit**

Commit message MUST:

- follow repository hook rules
- match format: `type(scope): summary`
- be CI-compliant

Do NOT include toolchain status lines.

## 15. Required Shared Skills

When available, MUST be used:

- `deterministic-change-workflow`
- `numpy-docstring-enforcer`
- `commit-block-generator`
- repository-specific workflow tools

If unavailable:

→ state explicitly
→ apply rules manually

## 16. Anti-Patterns (Forbidden)

- Guessing missing code
- Blind filesystem scanning when structured tools exist
- Re-implementing existing logic
- Introducing caching without clear invalidation
- Silent failures
- Skipping validation
- Modifying unrelated code

## 17. Session Stability

Continuously monitor for:

- context drift
- assumption creep
- loss of file grounding

If detected:

→ STOP
→ Recommend RESET

## 18. When in Doubt

STOP and ask for clarification.

Never proceed with assumptions.

## 19. Future Extensions

This contract may evolve to include:

- release workflows
- audit procedures
- indexing/retrieval policies
