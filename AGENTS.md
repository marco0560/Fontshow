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

-> STOP
-> Ask for clarification

## 2. Sources of Truth (SOT)

Priority order:

1. Repository files (filesystem)
2. Tests (`tests/`) -> authoritative behavior contract
3. Project documentation (`docs/`)
4. User instructions

Previous assistant output is NOT a source of truth.

If something is not visible -> STOP.

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

-> STOP
-> Ask for clarification

## 4. Repository-Specific Constraints

These constraints define the **real behavior surface** of the system.

- CLI behavior and output format are stability contracts
- Configuration and preflight behavior are part of the user-facing contract
- Deterministic output is required across environments
- Optional features must remain optional
- Performance regressions are considered bugs
- Changes must not silently alter user-visible behavior

If a change affects any of the above:

-> Treat as high risk
-> Validate explicitly

## 5. Execution Workflow (MANDATORY)

For any non-trivial task:

1. Analyze request
2. Identify missing information
3. Ask clarification questions if needed
4. Propose a concrete plan
5. WAIT for approval
6. Execute the plan
7. Validate (Section 8)
8. Ensure behavioral correctness (tests)
9. Produce commit block (if applicable)

Do NOT skip steps.

## 6. Deterministic Exploration

Before modifying code:

1. Verify symbols:

    ```bash
    rg <query>
    ```

2. Use repository tools when available (index/context systems)
3. Read actual source files before editing

Never modify code based only on assumptions.

## 7. Change Strategy

- Prefer multiple small commits over large changes
- Limit changes to one subsystem when possible
- Decompose complex work into incremental steps
- Avoid mixing refactor, feature, and bugfix in a single change

## 8. Validation Contract

All required checks MUST pass before concluding.

Preferred:

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

- Fix all failures BEFORE concluding
- Do not ignore warnings/errors
- Do not weaken tests to pass validation

## 9. Targeted Validation

- Identify affected subsystems
- Run focused tests first (fast feedback)
- Run full test suite before commit

## 10. Test Contract

Tests are the authoritative behavioral specification.

Requirements:

- Deterministic
- Environment-independent
- No reliance on external systems unless explicitly allowed

Forbidden:

- Weakening assertions
- Introducing flakiness
- Bypassing failing tests

If tests contradict assumptions -> tests win.

## 11. Strict Patch Discipline

All code changes MUST be provided as:

- explicit file paths
- exact OLD block (byte-identical)
- exact NEW block

Rules:

- No summaries
- No partial edits
- No reconstructed context
- No “approximate matches”

If OLD block cannot be matched exactly -> STOP.

## 12. Architecture Constraints

Respect separation of concerns.

Example pattern:

| Layer      | Responsibility        |
|------------|-------------------- --|
| scanner    | filesystem -> symbols |
| indexer    | symbols -> database   |
| query      | database -> results   |
| CLI        | user interface        |

Rules:

- Do not mix layers
- Do not bypass abstractions
- Do not duplicate existing logic

## 13. Build System & Generated Artifacts

- Keep build configuration and outputs in sync
- Do not manually edit generated files
- Modify generators and regenerate outputs instead
- Treat build or packaging regressions as real bugs

## 14. Coding Standards

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

## 15. Error Handling

- Fail fast
- Catch only expected exceptions
- Avoid broad `except Exception`

## 16. Regression Policy

The following are considered bugs:

- platform-specific breakages
- optional feature regressions
- performance regressions
- CLI or output contract changes

## 17. Debugging Discipline

- Reproduce the issue before fixing
- Identify root cause before writing code
- Avoid speculative fixes

## 18. Hidden Complexity Rule

If code appears complex or redundant:

- Assume it encodes real edge cases
- Check history/tests before simplifying
- Do not “clean up” without proof

## 19. Commit Contract

If committing or proposing a commit:

- Use `commit-block-generator` if available
- Produce a **single atomic commit**

Commit message MUST:

- follow repository hook rules
- match format: `type(scope): summary`
- be CI-compliant

Commit body MUST include:

- root cause
- implemented fix
- validation performed (when applicable)

Do NOT include toolchain status lines.

## 20. Required Shared Skills

When available, MUST be used:

- `deterministic-change-workflow`
- `numpy-docstring-enforcer`
- `commit-block-generator`
- repository-specific workflow tools

If unavailable:

-> state explicitly
-> apply rules manually

## 21. Anti-Patterns (Forbidden)

- Guessing missing code
- Blind filesystem scanning when structured tools exist
- Re-implementing existing logic
- Introducing caching without clear invalidation
- Silent failures
- Skipping validation
- Modifying unrelated code

## 22. Session Stability

Continuously monitor for:

- context drift
- assumption creep
- loss of file grounding

If detected:

-> STOP
-> Recommend RESET

## 23. Engineering Heuristics

- Small changes can have wide effects
- Complex code often encodes edge cases
- Prefer correctness over elegance
- Validate changes beyond the immediate scope
- When duplication spreads, extract shared logic

## 24. When in Doubt

STOP and ask for clarification.

Never proceed with assumptions.

## 25. Future Extensions

This contract may evolve to include:

- release workflows
- audit procedures
- indexing/retrieval policies
