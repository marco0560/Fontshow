# Project Decisions (Reverse-Chronological)

This document records the **active and historical technical decisions**
taken during the development of **Fontshow**.

Decisions are listed in **reverse chronological order**:
- the **most recent decisions appear first**;
- older decisions follow below.

This makes the document easier to read as a *current state description*,
while still preserving rationale and context.

All decisions in this file are considered **binding** unless explicitly superseded.

Any changes to these decisions must be:
- explicitly discussed;
- reflected in this document;
- traceable through dedicated commits.

## Coverage Strategy and Rationale

**Status:** Accepted
**Date:** 2026-01-05
**Scope:** Test coverage policy for Fontshow

### Context

Fontshow includes a mix of:

- **Core logic modules** (validation, inference, preflight checks)
- **I/O-heavy pipeline components** (font discovery, catalog generation, LaTeX integration)
- **CLI entry points** and orchestration code

A full test suite is in place and currently executed on Linux (Gentoo) using `pytest` and `pytest-cov`.

At the time of this decision, the global coverage percentage reported by the tooling is relatively low (≈36%), despite all tests passing.

### Observations

Analysis of the coverage report shows that the low global percentage is primarily caused by two large modules:

- `fontshow/create_catalog.py`
- `fontshow/dump_fonts.py`

These modules:
- are heavily dependent on the host system (installed fonts, fontconfig, filesystem layout)
- interact with external tools (LuaLaTeX)
- perform long-running, side-effect-heavy operations
- are designed as **integration pipelines**, not as pure logic units

By contrast, the following areas show high coverage (typically 90–100%):

- Language and script inference
- Schema and semantic validation
- Inventory parsing and validation
- Preflight architecture (checks, registry, runner, rendering)
- Contract tests and policy enforcement

### Decision

The project **intentionally prioritizes meaningful, high-signal coverage** over a high global percentage.

Specifically:

- High coverage is required and enforced for:
  - core inference logic
  - validation and policy code
  - preflight checks and their contracts
- Low or zero coverage is currently accepted for:
  - CLI entry points
  - I/O-heavy pipeline modules
  - system-dependent integration code

The reported global coverage value is therefore considered **informational**, not a quality gate.

### Rationale

Attempting to raise global coverage by aggressively testing pipeline code would require:
- extensive mocking of system resources
- brittle test setups tied to specific Linux distributions
- tests that increase maintenance cost without improving confidence

Instead, the chosen approach:
- maximizes confidence in correctness where it matters
- keeps the test suite fast and deterministic
- aligns with the project’s long-term maintainability goals

### Consequences

- A low global coverage percentage is accepted and documented.
- Contributors are encouraged to add tests to core logic modules, not to inflate coverage numbers.
- Coverage reports must be interpreted per-module, not as a single aggregate metric.

### Future Work

Planned follow-up actions include:

- Introducing a `.coveragerc` file to:
  - exclude CLI entry points and selected pipeline modules
  - clarify the intended coverage scope
- Adding targeted tests for additional edge cases on native Linux (Gentoo)
- Potentially introducing integration-test markers for system-dependent paths

These improvements are explicitly deferred to a later phase.

**Decision summary:**
Coverage is treated as a qualitative signal, not a numerical target. The current strategy is intentional, documented, and aligned with the architecture of Fontshow.

## Decision: Script-aware sample text selection

**Status:** Accepted
**Context:** Font catalog generation (`create_catalog`)
**Related versions:** v0.20.0+

### Context

Fontshow supports rendering sample text for each font in the generated
catalog. Sample text can originate from two different sources:

1. **Embedded sample text**, extracted directly from the font file
   during `dump_fonts`.
2. **Inferred sample text**, selected at catalog generation time based
   on language inference results derived from Unicode coverage.

Previously, embedded sample text was always preferred whenever present,
regardless of its language or script compatibility with the dominant
font script. This behavior caused incoherent rendering for non-Latin
fonts (e.g. CJK fonts rendered with German or other Latin pangrams),
leading to cascading LuaLaTeX warnings and unreadable output.

### Decision

Embedded sample text is now used **only if its language matches the
primary inferred language** of the font.

If the embedded sample text language is incompatible with the dominant
inferred language, it is ignored and Fontshow falls back to selecting a
sample text based on language inference results.

Formally:

- Let `L₀` be the primary inferred language
  (`font["inference"]["languages"][0]`).
- Embedded sample text is used **only if**
  `sample_text.lang == L₀`.
- Otherwise, sample text is selected using inferred language-based
  fallback logic.

### Rationale

- Fontshow is an **analysis and cataloging tool**, not a raw font viewer.
- Script and language coherence is more important than strict fidelity
  to embedded font metadata.
- Embedded sample text is often Latin-based even in fonts whose dominant
  coverage is non-Latin.
- Using script-incompatible sample text leads to misleading output and
  LaTeX compilation issues.

This decision keeps inference policy centralized in
`parse_font_inventory` and ensures that `create_catalog` remains a pure
consumer of inference results.

### Consequences

- Catalog rendering is now consistent across scripts.
- Non-Latin fonts reliably render appropriate sample text.
- Embedded sample text is still preserved and used when compatible.
- No behavior change for purely Latin fonts.

### Alternatives considered

- Always prefer embedded sample text (rejected: causes incoherent output).
- Add user-facing flags to choose precedence (postponed; increases
  complexity without clear immediate benefit).

## Decision: Preflight checks refactoring to a class-based, registry-backed model

**Status**: Accepted
**Date**: 2026-01-04
**Scope**: `fontshow.preflight`

### Context

The original preflight subsystem started as a function-based implementation,
where each check was exposed as a standalone function and orchestrated by the
runner through a static dispatch table.

As the number of checks and policies grew, several issues emerged:

- Tests required extensive monkeypatching of internal functions.
- There was no explicit contract defining what a “check” was.
- Adding or composing checks for testing purposes was fragile.
- Static analysis tools (ruff, pylance) conflicted with dynamic dispatch.
- The runner API became increasingly difficult to reason about.

At the same time, we needed to preserve:
- Deterministic execution order
- `enabled` / `disabled` filtering semantics
- Test isolation and safety
- Backward-compatible CLI behavior

### Decision

We refactored the preflight subsystem to a **class-based model**, centered around
an explicit abstract base class and a lightweight registration mechanism.

The main elements of the new design are:

#### 1. `BaseCheck` abstract contract

All preflight checks now subclass a common abstract base class:

- Enforces the presence of:
  - a `check_id` class attribute
  - a `run()` method returning a `CheckResult`
- Provides a clear, inspectable contract for both production code and tests
- Enables static tooling to reason about the system

This makes the notion of “a check” explicit and verifiable.

#### 2. Explicit registry for checks

Checks are registered automatically when their class is defined.

The registry:
- Tracks all known check classes
- Allows test-only or experimental checks to exist without polluting the runner
- Supports controlled extensibility without dynamic imports

Importantly, **built-in checks remain explicitly listed** in the runner via
`CHECKS`, preserving clarity and determinism.

#### 3. Runner as a stable, testable orchestration layer

The runner now:

- Exposes its dependent modules (`environment`, `font_discovery`, `latex`)
  explicitly to support safe and explicit monkeypatching in tests
- Resolves checks using a clear priority order:
  1. Explicit `checks` argument (advanced usage, tests)
  2. Registered checks
  3. Built-in `CHECKS` fallback
- Preserves `enabled` / `disabled` filtering semantics

This results in a runner that is:
- Predictable
- Test-friendly
- Statistically analyzable
- Backward-compatible

### Consequences

**Positive**
- Stronger contracts and clearer architecture
- Tests assert behavior, not implementation details
- Reduced friction between runtime flexibility and static analysis
- Preflight subsystem is now considered **stable**, not experimental

**Trade-offs**
- Slightly higher upfront complexity compared to a function-based approach
- Requires discipline to keep test-only checks isolated

### Notes

- Sentinel or test-only checks may exist in the registry but are never executed
  by the runner unless explicitly requested.
- Contract tests ensure all production checks comply with `BaseCheck`.
- This design intentionally avoids implicit auto-discovery via imports.

### References

- `fontshow/preflight/checks/base.py`
- `fontshow/preflight/runner.py`
- `tests/preflight/test_base_check_contract.py`

## Decision: Move preflight subsystem to a class-based design

### Context

The initial implementation of the preflight subsystem was function-based.
While simple, this approach quickly showed limitations when introducing:

- Fine-grained policy tests (environment matrix, capability checks)
- Selective execution (enabled / disabled checks)
- Deterministic ordering and extensibility
- Robust monkeypatching in tests without relying on import hacks

Several iterations revealed that a purely function-based model made the
runner harder to test and reason about as the system grew.

### Decision

We refactored the preflight subsystem to a **class-based design**, centered on
an explicit `BaseCheck` abstract contract.

Each preflight check is now represented by a class that:

- Exposes a stable `check_id`
- Implements a `run() -> CheckResult` method
- Encapsulates its own execution logic

The runner (`run_preflight`) executes checks by instantiating these classes
from a deterministic registry (`CHECKS`).

### Why a BaseCheck abstract class

Introducing `BaseCheck` provides:

- A clear and enforceable contract for all checks
- Static guarantees (via typing) about the check interface
- A foundation for future validation and tooling

A dedicated test ensures that all registered checks comply with this contract,
preventing silent divergence over time.

### Why the runner exposes modules explicitly

The runner intentionally exposes the following modules as part of its public API:

- `environment`
- `font_discovery`
- `latex`

This design allows tests to safely monkeypatch environment detection and
capability probes without relying on fragile import-path tricks.

This is a deliberate trade-off favoring **testability and transparency**
over strict encapsulation.

### Check selection semantics

The runner supports selective execution through:

- `enabled`: run only checks whose `check_id` is included
- `disabled`: skip checks whose `check_id` is included

If both are provided, `enabled` is applied first, then `disabled`.

The `CHECKS` registry remains the authoritative list of built-in checks and is
not dynamically extended at runtime.

### Status

With this refactor and the accompanying test coverage, the preflight subsystem
is now considered **stable** rather than experimental.

## Decision: Transition to a Class-Based Model for Preflight Checks

**Status:** Accepted
**Area:** Preflight / Testing / Architecture
**Date:** 2026-01-03

### Context

The preflight checking system was initially implemented using a
**function-based model**, where the runner directly invoked functions
such as `check_environment()`, `check_font_discovery()`, etc.

As the project evolved and a more comprehensive test suite was introduced
— especially *policy-oriented tests* — several structural limitations
became evident:

- difficulty performing **selective monkeypatching** of dependencies
- implicit coupling between the runner and check implementations
- lack of a shared abstraction representing the concept of a “check”
- weaker domain semantics: a function does not model a first-class entity

In particular, the test suite required:

- explicit access to `check_id`
- fine-grained inspection of `CheckResult` objects
- controlled simulation of OS, execution mode, and tool availability
- long-term stability of the API used by tests

### Decision

The preflight subsystem was refactored to adopt a **class-based model**,
where each check is represented by a class exposing a `run()` method
that returns a `CheckResult`.

The runner maintains an **explicit registry of check classes** and is
responsible solely for orchestration.

Conceptual example:

```python
class FontDiscoveryCheck:
    check_id = "font_discovery.capability"

    def run(self) -> CheckResult:
        ...
```

### Rationale

The class-based model provides:

- an explicit representation of the *check* domain concept
- clearer execution flow
- more readable, stable, and less fragile tests
- a clean separation between:
  - check logic
  - orchestration (runner)
  - output rendering (CLI)

This approach also enables the future introduction of an
**abstract base class (`BaseCheck`)** to serve as a formal contract
for all preflight checks.

### Consequences

- Slightly increased verbosity in the implementation
- Significantly improved robustness, extensibility, and maintainability
- Easier and safer addition of new checks


## Decision: Explicit Exposure of Check Modules in the Runner

**Status:** Accepted
**Area:** Testing / Public API
**Date:** 2026-01-xx

### Context

The test suite relies on `pytest.monkeypatch` to simulate different
environmental conditions (OS, execution mode, tool availability).

To do so, tests intentionally reference symbols such as:

```python
runner.environment.detect_os
runner.font_discovery.has_fontconfig
runner.latex.has_lualatex
```

Linting tools such as **ruff** tend to flag these imports as unused or
attempt to remove them, as their usage is indirect.

### Decision

The `fontshow.preflight.runner` module explicitly exposes the following
modules as part of its **intentional public API**:

- `environment`
- `font_discovery`
- `latex`

This is a deliberate design choice and is documented as such.

### Rationale

- the test suite intentionally depends on these symbols
- the runner acts as a stable *facade* for the preflight subsystem
- this avoids fragile solutions (`# noqa`, dynamic imports, test-only hacks)

### Consequences

- the runner exposes a slightly broader public surface
- the relationship between tests and code becomes explicit and understandable
- instability between linting and runtime behavior is eliminated

## Decision: Font discovery preflight checks rely on fc-list only

**Status**: Accepted
**Context**: Preflight stage (C5.3)
**Date**: 2026-01-03

### Decision

The preflight stage checks for font discovery capability by verifying the
presence of `fc-list` (fontconfig).

The presence of `fc-query` is intentionally **not** verified at preflight time.

### Rationale

- In standard Linux distributions, `fc-list` and `fc-query` are installed
  together as part of fontconfig.
- The preflight stage is intended to perform *capability checks*, not full
  runtime validation.
- Full font inspection (which requires `fc-query`) is performed during the
  pipeline execution and validated at runtime.
- Checking `fc-query` at preflight time could lead to premature failures in
  minimal or CI environments without providing actionable benefit.

### Consequences

- Preflight may succeed even if `fc-query` is missing.
- Missing `fc-query` will be detected later by the pipeline stages that require it.
- This decision simplifies the preflight logic and keeps it aligned with its
  intended scope.

### Future considerations

A pluggable font discovery backend architecture is planned for v2.x.y.
At that stage, backend-specific requirements (including `fc-query`) will be
validated as part of backend selection and runtime readiness checks.

## Decision: Font Discovery

### Context

Font discovery is currently capability-based.

### Decision

A pluggable backend architecture is intentionally deferred to v2.x.y.

## Decision: Commit Signing Enforcement and CI Automation

### Context

The project requires strong guarantees about the integrity and provenance
of commits on the `main` branch.

The initial goal was to achieve **all of the following simultaneously**:

1. All commits cryptographically signed and verified by GitHub
2. Fully automated releases using `semantic-release` running in GitHub Actions
3. GitHub acting as the sole enforcer and source of truth

### Attempted Approaches

Several configurations were evaluated:

#### A. Branch Protection Rules with “Require signed commits”

- Result: ❌ CI commits rejected
- Reason: GitHub Actions cannot produce commits with *verified* signatures

#### B. Repository Rulesets with signed-commit enforcement

- Result: ❌ Same limitation as above
- Rulesets enforce signing correctly but do not distinguish CI-generated commits

#### C. GPG / SSH signing inside GitHub Actions

- Result: ❌ Not viable
- GitHub does not associate CI-generated signatures with a verified identity

#### D. Forcing semantic-release to avoid commits

- Result: ⚠️ Partial
- Would require abandoning `@semantic-release/git`
- Incompatible with current release workflow

### Decision

Fontshow adopts the following model:

- GitHub **Repository Rulesets** enforce commit signing
- **Human-authored commits must be signed**
- **CI automation is explicitly trusted and documented**
- GitHub remains the authoritative enforcement layer

This is the **only configuration that is both technically feasible
and auditable** with current GitHub capabilities.

### Consequences

- Local hooks are advisory, not authoritative
- CI automation is trusted by policy, not by cryptographic proof
- The decision may be revisited if GitHub introduces verified CI signatures

## Decision: Version bumps driven by Conventional Commits

### Decision

Fontshow version increments are driven exclusively by **Conventional Commits**
in combination with `semantic-release`.

- `fix:` → patch release
- `feat:` → minor release
- `BREAKING CHANGE:` → major release

The effective version is materialized via Git tags and resolved at runtime.

### Rationale

- Version numbers reflect semantic changes
- No manual version editing in source files
- Git history becomes part of the public API contract

### Consequences

- Incorrect commit types produce incorrect versions
- Developers must treat commit messages as authoritative

## Decision: Single-source-of-truth versioning

### Decision

Fontshow uses a **single-source-of-truth versioning model**:

- Version defined in `pyproject.toml`
- Retrieved at runtime via:

```python
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("fontshow")
except PackageNotFoundError:
    __version__ = "0.0.0"
```

- All CLI tools import the version from `fontshow.__version__`

### Consequences

- Git tags, package metadata, CLI output and generated artifacts are consistent
- No duplicated version constants

## Decision: Deferred Warning Emission via Structured Collection

### Decision

Validation warnings are **not emitted directly**.
They are collected as structured records and returned to the caller.

### Rationale

- Deterministic testing
- Configurable verbosity
- Machine-readable export

### Consequences

- CLI flags (`--verbose`, `--quiet`) control presentation only
- Core logic remains side-effect free
- Warning handling via structured accumulator
- No printing in leaf validators

## Decision: Coverage reporting without enforcement

### Decision

Test coverage is measured and reported, but **no minimum threshold is enforced**.

### Rationale

- Some code interacts with external systems
- Coverage is informative, not a gate

**Status**
Accepted

## Decision: CI quality gates via pre-commit and pytest

### Decision

The **test job** in CI enforces quality via:

- `pre-commit run --all-files`
- `pytest`

The **docs job** only builds documentation.

### Rationale

- Clear separation of concerns
- CI mirrors local developer workflow

### Consequences
- The CI pipeline fails early if code quality checks do not pass
- Tooling such as `ruff` is managed exclusively via `.pre-commit-config.yaml`
- Additional quality gates (coverage, type checking) can be added to the test job
  without affecting documentation deployment
- Developers can rely on CI to mirror local pre-commit behavior

## Decision: Separate CI jobs for tests and documentation

### Decision

Tests and documentation are executed in **separate CI jobs**.

### Rationale

- Failures are easier to diagnose
- Documentation issues do not block test feedback

## Decision: Font entry `family` field required at top-level

### Decision

Each font entry **must** include a top-level `family` field.

### Rationale

- Unambiguous grouping
- Simple and deterministic validation

## Decision C4.2.2 — Script inference based on Unicode coverage

### Decision

Script inference is performed using Unicode coverage metadata
and normalized to **ISO 15924** codes.

Fallback logic is used when block-level data is unavailable.
The inference strategy follows a two-step approach:

1. **Primary source**: Unicode block statistics (`coverage.unicode_blocks`)
2. **Fallback**: Maximum Unicode code point (`coverage.unicode.max`)

All outputs are normalized to ISO 15924 codes and stored in
`fonts[].inference.scripts`.

If no reliable inference is possible, the value `["unknown"]` is emitted.

### Context

Fontshow needs a consistent and portable way to infer the writing systems
supported by a font, independently of platform-specific metadata and
language declarations.

Available inputs include:
- Unicode block usage statistics (FontConfig / fc-query)
- Unicode code point coverage (fontTools)

### Rationale

- Unicode coverage is more stable and portable than language tags.
- ISO 15924 provides a compact, standardized representation of writing systems.
- Separating scripts from languages avoids false assumptions and simplifies
  downstream processing.
- The fallback mechanism ensures robustness when block-level data is unavailable.

### Consequences

- `fonts[].inference.scripts` is best-effort and non-authoritative.
- Downstream tools must tolerate `"unknown"` and missing values.
- Language inference is handled separately and may not align one-to-one with
  script inference.

## Exclude coverage artifacts from version control

### Decision

Coverage artifacts generated by `pytest-cov` (e.g. `.coverage`,
`coverage.xml`, `htmlcov/`) are excluded from version control and treated
as disposable local artifacts.

### Rationale
These files are environment-specific, non-deterministic, and can be
regenerated at any time. Storing them in the repository would add noise
without long-term value.

## Work tracking and technical debt

- TODOs, bugs, and technical debt are tracked **exclusively via GitHub Issues**.
- Static TODO files in the repository are not used.
- Issues represent the operational state of the work.

## Development environment

- Development takes place in Linux and Linux-like environments (including WSL).
- Differences between environments are considered part of the problem domain.
- Validation on native Linux is considered necessary for critical functionality.

## Testing and quality

- Automated tests are based on **pytest**.
- Quality checks include linting and static validation tools.
- CI is considered the final authority on code quality.

## Documentation

- Official project documentation is maintained using **MkDocs**.
- The README and cheat-sheets are derived from the MkDocs documentation.

## Data handling

- Raw data is not modified or “cleaned” silently.
- Normalization:
  - does **not replace** original values;
  - adds normalized versions alongside the original data.
- The  **Schema** and the **Data Dictionary** are the normative reference for the meaning of data fields.

## Language and project structure

- **Python** is the primary language of the project.
- The project is structured as a **package**, not as a collection of standalone scripts.
- Module execution is preferably performed using:
  - `python -m <module>`
