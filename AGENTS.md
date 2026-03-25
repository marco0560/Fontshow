# AGENTS.md — Fontshow Codex Operating Contract

## 0. Mission

You are operating on the Fontshow repository.

This is a **deterministic, test-driven engineering project**.

Priority:

1. Correctness
2. Test integrity (local + CI)
3. Reproducibility
4. Traceability
5. Minimality of change

Fluency is irrelevant.

---

## 1. Operating Mode

Mode: HARD-FAIL DETERMINISTIC

Rules:

- Never guess
- Never infer missing code
- Never reconstruct unseen files
- Never approximate behavior

If any required information is missing:

→ STOP
→ Ask for clarification

---

## 2. Sources of Truth

Priority order:

1. Repository files
2. Tests (`tests/`) — **authoritative behavior contract**
3. Project documentation (`docs/`)
4. User instructions

Previous assistant output is NOT a source of truth.

---

## 3. Mandatory Work Cycle (STRICT)

All tasks MUST follow this exact sequence:

### Step 1 — PLAN

- Provide a **minimal, explicit plan**
- Identify impacted files
- Identify risks
- Ask ALL necessary clarification questions

→ STOP and WAIT

---

### Step 2 — USER CONFIRMATION

- Do NOT proceed without approval
- Accept modifications to the plan

---

### Step 3 — EXECUTION

- Apply minimal, surgical changes
- Respect all constraints in this file

---

### Step 4 — TEST EXTENSION (if needed)

- Add tests when:
  - behavior changes
  - bug is fixed
  - new invariant introduced

Tests must:

- be deterministic
- not depend on environment-specific tools
- not require LaTeX installation

---

### Step 5 — FULL VALIDATION

You MUST assume the following commands are run:

```bash
pre-commit run --all-files
pytest -q
```

`pre-commit` includes and replaces:

```bash
black .
ruff check .
mypy src/fontshow
```

All must pass.

If any would fail:

→ fix BEFORE concluding

---

### Step 6 — COMMIT BLOCK

Propose a **single commit block** that is:

- 15 - 20 lines long
- atomic
- CI-compliant, checked against `.githooks/commit-msg.py`

Include:

- type from permitted list
- scope from permitted list
- `Closes: #<issue_number>` if the activity closes an issue
- `Refs:` if there is a reference to a decision or to an issue

DO NOT include:

- tool output
- check summaries
- noise

### repoindex (tool) Workflow

Use `repoindex` as a repository-local developer tool.

Assume the session runs inside the repository virtual environment.
All tool and command paths MUST resolve against that environment.
When invoking tools or commands, prefer the virtual environment's
executables and environment-derived paths over system-wide ones.

Before broad code exploration or patching:

1. Activate the repository virtual environment.
2. Run `repoindex index`.
3. Verify candidate symbols with `rg <query>` before editing.
4. Run `repoindex context-for "<query>" --json` or `--prompt` as needed.
5. Inspect the referenced files before applying changes.

Use output modes as follows:

- plain `context-for`: compact human-readable context
- `context-for --json`: structured tool/agent workflows
- `context-for --prompt`: copy-ready agent preamble
- `context-for --explain`: retrieval diagnostics

`repoindex` narrows search and improves determinism. It does not replace
reading the actual source files before editing.

---

## 4. Docstring Policy (CRITICAL)

### 4.1 Coverage

Every:

- module
- class
- public function
- private function

MUST have a docstring.

Absence is a defect.

---

### 4.2 Style (MANDATORY)

Docstrings MUST follow **NumPy style**.

Structure:

```text
Short summary.

Parameters
----------
param : type
    Description.

Returns
-------
type
    Description.

Raises
------
ExceptionType
    Condition.

Notes
-----
<Description>

Examples
--------
>>> func(input)
output
```

The `Notes` field is optional. It is required if there is / are:

- Non-obvious behavior: Anything that a reader would not infer from the signature or name.
- Implementation details that affect correctness: especially if they influence edge cases or performance.
- Important invariants or assumptions.
- Design decisions / rationale.
- Domain-specific meaning

The `Examples` field is optional. It is required if:

- The function is not immediately obvious from its signature
- There are non-trivial inputs or outputs
- Edge cases matter
- Behavior is easier to show than to explain
- CLI-like or pipeline functions
- String transformations / formatting functions

---

### 4.3 Requirements

Docstrings must:

- match actual behavior (no drift)
- reflect current signature
- include `Raises` when exceptions are possible
- avoid redundancy
- be concise and precise

---

### 4.4 Enforcement Rules

If modifying a function/class/module:

→ ALWAYS verify docstring compliance

If missing or non-compliant:

→ FIX as part of the same change

---

## 5. Testing and CI Constraints (CRITICAL)

### 5.1 CI Environment

GitHub CI does **NOT guarantee LaTeX availability**.

Therefore:

- Tests MUST NOT require:
  - `lualatex`
  - external binaries not mocked

---

### 5.2 Preflight / LaTeX behavior

Code MAY depend on LaTeX.

Tests MUST:

- mock it
- bypass it
- or test behavior without requiring it

---

### 5.3 Determinism

Tests MUST be:

- deterministic
- environment-independent
- reproducible

---

### 5.4 Test Integrity

Never:

- weaken assertions
- skip tests without reason
- introduce flaky behavior

---

## 6. Scope Control

Do ONLY what is requested.

Do NOT:

- refactor unrelated code
- rename symbols
- introduce stylistic changes
- modify APIs

Unless explicitly required.

---

## 7. Repository Awareness

Key subsystems:

- CLI: `src/fontshow/cli/`
- Inventory: `src/fontshow/inventory/`
- Catalog: `src/fontshow/catalog/`
- Preflight: `src/fontshow/preflight/`
- Ontology: `src/fontshow/ontology/`

Tests mirror system contracts.

---

## 8. Issues and Milestones Awareness

The repository includes structured planning artifacts in the root:

- `issues.json`
- `milestones_plan.json`

These files define:

- current backlog
- issue scope and intent
- milestone grouping and priorities

### Usage Rules

When performing non-trivial work:

- Consult these files (if relevant to the task)
- Align changes with:
  - existing issues
  - declared milestones
- Do NOT introduce work that conflicts with planned scope

### Constraints

- Do NOT invent new issues or milestones unless explicitly requested
- Do NOT reinterpret issue intent
- Treat these files as **planning source of truth**

### When to Use

Use these artifacts when:

- implementing features
- fixing bugs tied to roadmap items
- performing refactors related to tracked work
- planning multi-step changes

Skip them for:

- trivial fixes
- purely local changes
- mechanical tasks (e.g. formatting, docstrings only)

---

## 9. Change Discipline

Changes must be:

- minimal
- localized
- reversible
- consistent with existing architecture

Avoid:

- cross-module ripple effects
- hidden behavior changes

---

## 10. Failure Conditions (STOP)

STOP immediately if:

- ambiguity in requirements
- missing file context
- unclear expected behavior
- risk of breaking CLI contract
- risk of breaking tests

---

## 11. Session Stability

Monitor for:

- context drift
- assumption creep
- loss of file grounding

If detected:

→ recommend RESET

---

## 12. Audit Mode (optional)

When explicitly requested:

- enforce 100% docstring coverage
- report violations before fixing
- operate in batch mode

---

END
