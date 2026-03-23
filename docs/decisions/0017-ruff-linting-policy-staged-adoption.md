# Decision 0017 - Ruff Linting Policy and Staged Adoption

**Date**: 05/02/2026
**Status**: Accepted

## Context

Fontshow uses Ruff as its primary static analysis tool.
A full strict rule set was found to generate excessive noise on legacy modules
(e.g. `src/fontshow/cli/dump_fonts.py`), obscuring high-value diagnostics and slowing
development.

The project adopts a **staged, policy-driven Ruff adoption strategy** that
prioritizes correctness and architectural insight over style enforcement.

## Principles

- CI is the **source of truth**
- Ruff configuration must be **explicit and intentional**
- Rule families are enabled **one category at a time**
- Legacy code is not refactored solely to satisfy linting
- New code is expected to comply with progressively stricter rules

## Baseline (Phase C – current)

Global Ruff configuration is intentionally relaxed to enforce only:

- `E` – pycodestyle errors (real syntax / logic issues)
- `F` – pyflakes (undefined names, unused imports, etc.)
- `I` – import correctness

All other rule families are temporarily disabled.

This establishes a **quiet, stable baseline** aligned with CI.

## Staged Re-enablement Plan

Rule families will be re-enabled in the following order.

Each phase requires:

- explicit decision
- CI passing
- no unrelated refactors

### Phase 1 — Exception semantics (highest value)

#### Where enforced

- Global config, with per-file ignores allowed for legacy modules

#### Rule families

- `BLE`   (blind except)
- `TRY`   (exception construction)
- `EM`    (exception message handling)
- `S110`  (try/except/pass)
- `S112`  (try/except/continue)

##### Rationale

- Direct impact on CLI behavior, logging, and diagnosability
- Aligns with Fontshow logging and TRACE policies

---

### Phase 2 — Runtime vs typing boundary

#### Rule families phase 2

- `TC`

#### Rationale phase 2

- Prevents runtime imports being hidden in `TYPE_CHECKING`
- Improves correctness without stylistic churn

---

### Phase 3 — Filesystem & path correctness

#### Rule families phase 3

- `PTH`

#### Rationale phase 3

- Improves cross-platform robustness (Linux / WSL / Windows)
- Behavior-preserving when applied deliberately

---

### Phase 4 — Complexity mapping (informational)

#### Rule families phase 4

- `C901`
- `PLR0911`
- `PLR0912`
- `PLR0915`

#### Rationale phase 4

- Used to identify hotspots
- Not enforced as hard failures initially
- Guides future refactoring work

---

### Phase 5 — Security checks (explicit opt-in)

#### Rule families phase 5

- `S603` (subprocess)
- `S324` (hashlib)

#### Rationalecphase 5

- Relevant only where untrusted input is involved
- Requires contextual review

---

### Phase 6 — Optional / style-level rules (lowest priority)

#### Rule families phase 6

- Typing: `ANN`, `FBT`
- Docstrings: `D`
- Formatting: `COM`, `E501`
- Hygiene: `TD`, `ERA`, `FIX`
- Micro-refactors: `SIM`, `FURB`, `PERF`, `ARG`

#### Rationale phase 6

- High churn, low architectural value
- Enabled only if the project explicitly adopts stricter style standards

## Enforcement Model

- CI enforces only the currently active phase
- VS Code mirrors CI configuration
- No rule family is enabled implicitly
- Per-file ignores are allowed for legacy modules during transition

## Consequences

- Ruff remains a high-signal tool
- Linting does not drive refactoring by accident
- Policy decisions are explicit and reversible
- Long-term code quality improves incrementally
