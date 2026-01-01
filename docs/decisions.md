# Active Project Decisions

This document lists the **currently active project decisions** for Fontshow.

It does **not** include:
- historical background;
- discarded alternatives;
- past motivations.

For historical context and the evolution of decisions, refer to the **Development Diary**.

## Language and project structure

- **Python** is the primary language of the project.
- The project is structured as a **package**, not as a collection of standalone scripts.
- Module execution is preferably performed using:
  - `python -m <module>`

## Pipeline architecture

- The pipeline is divided into **independent stages**.
- Each stage has:
  - explicit inputs;
  - explicit outputs;
  - well-defined responsibilities.
- Intermediate artifacts (inventories, JSON files, LaTeX files) are considered an **integral part of the project**, not temporary by-products.

## Data handling

- Raw data is not modified or “cleaned” silently.
- Normalization:
  - does **not replace** original values;
  - adds normalized versions alongside the original data.
- The **Data Dictionary** is the normative reference for the meaning of data fields.

## Documentation

- Official project documentation is maintained using **MkDocs**.
- Markdown files under `docs/` constitute the **operational manual**.
- Automatically generated documentation based on code extraction is **not used**.
- The README and cheat-sheets are derived from the MkDocs documentation.

## Testing and quality

- Automated tests are based on **pytest**.
- Quality checks include linting and static validation tools.
- CI is considered the final authority on code quality.

## Work tracking and technical debt

- TODOs, bugs, and technical debt are tracked **exclusively via GitHub Issues**.
- Static TODO files in the repository are not used.
- Issues represent the operational state of the work.

## Development environment

- Development takes place in Linux and Linux-like environments (including WSL).
- Differences between environments are considered part of the problem domain.
- Validation on native Linux is considered necessary for critical functionality.

## Decision: font entry `family` field is required at top-level

### Context
During the introduction of automated validation tests (`validate_font_entry`),
it became clear that the validator requires a `family` field at the top level
of each font entry. The presence of `identity.family` alone is not sufficient
to pass validation.

### Decision
For the current architecture, a font entry is considered structurally valid
only if a `family` field is present at the top level of the entry.

The `identity` object is treated as supplementary metadata and is not used
for structural validation.

### Rationale
- Ensures a single, unambiguous family identifier for grouping and indexing
- Keeps validation simple and deterministic
- Avoids implicit fallback logic during validation

### Consequences
- Test fixtures must include `family` at top-level
- Future refactors may unify `family` and `identity.family`
- A compatibility migration may be required if validation rules change

## Decision: Separate CI jobs for tests and documentation

### Context
Fontshow includes both an automated test suite (pytest) and
documentation built with MkDocs. Initially, both activities
were executed within a single CI job.

This caused unrelated failures (e.g. documentation warnings)
to block test execution and made CI diagnostics harder.

### Decision
The CI pipeline is structured into separate jobs:
- a **test** job running the pytest test suite
- a **docs** job building the documentation with MkDocs

The documentation job depends on the successful completion
of the test job.

### Rationale
- Tests and documentation have different responsibilities
- Isolating jobs simplifies debugging and failure analysis
- Prevents documentation issues from masking test failures
- Aligns with common best practices in Python projects

### Consequences
- Dependencies are installed separately per job
- CI execution remains deterministic and easier to maintain
- The pipeline can be extended later (coverage, linting)
  without affecting existing jobs

## Decision: CI quality gates via pre-commit and pytest

### Context
Fontshow uses `pre-commit` hooks (including `ruff`) to enforce code quality
and formatting rules locally at commit and push time.
The project also includes an automated test suite based on `pytest`.

Initially, CI responsibilities were not clearly separated, and some quality
checks risked being duplicated or inconsistently applied between local
development and CI.

### Decision
The CI pipeline enforces code quality and correctness through two distinct
mechanisms within the **test job**:

- **pre-commit** is executed with `pre-commit run --all-files`
- **pytest** is executed to validate program logic and data contracts

The **docs job** is responsible only for documentation building and deployment
and does not run pre-commit or test checks.

### Rationale
- `pre-commit` represents the authoritative source for code quality rules
  (formatting, linting, static checks)
- Running pre-commit in CI guarantees consistency with the local developer workflow
- Separating concerns avoids duplicated tooling configuration (e.g. installing ruff twice)
- Documentation failures should not be caused by code-style issues

### Consequences
- The CI pipeline fails early if code quality checks do not pass
- Tooling such as `ruff` is managed exclusively via `.pre-commit-config.yaml`
- Additional quality gates (coverage, type checking) can be added to the test job
  without affecting documentation deployment
- Developers can rely on CI to mirror local pre-commit behavior

This decision complements the separation of CI jobs for tests and documentation,
ensuring that each job enforces only the responsibilities relevant to its scope.

## Coverage reporting without enforcement

**Decision**
Test coverage is measured using `pytest-cov` and reported in CI logs,
but no minimum coverage threshold is enforced.

**Rationale**
Fontshow includes logic interacting with external tools and system
configuration, which is difficult to test exhaustively. Coverage is
used to guide testing priorities without blocking development.

**Status**
Accepted

## Exclude coverage artifacts from version control

**Decision**
Coverage artifacts generated by `pytest-cov` (e.g. `.coverage`,
`coverage.xml`, `htmlcov/`) are excluded from version control and treated
as disposable local artifacts.

**Rationale**
These files are environment-specific, non-deterministic, and can be
regenerated at any time. Storing them in the repository would add noise
without long-term value.

**Status**
Accepted

## Deferred Warning Emission via Structured Collection

**Decision**
The dump phase does not emit warnings directly to stdout or stderr. Instead,
warnings are collected internally as structured records and returned to the
caller.

**Rationale**
Direct emission of warnings complicates testing, logging control, and future
CLI ergonomics. A structured accumulator allows warnings to be:
- tested deterministically,
- filtered or suppressed,
- logged at configurable verbosity levels,
- exported in machine-readable form.

**Consequences**
At this stage, warnings are collected but not yet exposed through CLI options.
Future steps may introduce flags such as `--quiet`, `--verbose`, or
`--warnings-json` without refactoring the core logic.

**Status**
Accepted (implementation pending)

### Decision: CLI Verbosity Control

Fontshow provides basic verbosity control through CLI flags.

- By default, only validation errors are printed.
- `--verbose` enables printing of validation warnings.
- `--quiet` suppresses all validation output.

Warnings are always collected internally as structured data and are not
discarded when output is suppressed.

This approach keeps the default behavior clean while allowing users to
inspect validation issues when needed.

Warning handling via structured accumulator

No printing in leaf validators

#### Versioning strategy

Fontshow uses a **single-source-of-truth versioning model** based on
Python package metadata.

- The project version is defined in `pyproject.toml`.
- At runtime, the version is retrieved via `importlib.metadata.version()`:

```python
  from importlib.metadata import version, PackageNotFoundError

  try:
      __version__ = version("fontshow")
  except PackageNotFoundError:
      __version__ = "0.0.0"
```

- All tools (`dump_fonts`, `parse_font_inventory`, `create_catalog`) import
  the version from `fontshow.__version__`.
- The version is exposed via the `--version` CLI option and embedded in
  generated artifacts.

This guarantees consistency between Git tags, packaging metadata,
CLI tools, and generated inventories.

### Decision: Version bumps driven by Conventional Commits

**Decision**
Fontshow version increments are driven exclusively by commit types
following the Conventional Commits specification, in combination with
semantic-release.

- `fix:` commits trigger a **patch** version bump (e.g. `0.8.0 → 0.8.1`)
- `feat:` commits trigger a **minor** version bump (e.g. `0.8.0 → 0.9.0`)
- `BREAKING CHANGE` triggers a **major** version bump

The effective version is materialized via Git tags and resolved at runtime
using `setuptools-scm`.

**Rationale**
This ensures that:
- version numbers reflect actual semantic changes;
- tooling (`pip install -e .`, CLI `--version`, generated artifacts)
  always reports a version consistent with Git history;
- no manual version editing is required in source files.

**Consequences**
- A commit type mismatch (e.g. using `feat:` instead of `fix:`)
  will intentionally produce a higher version number.
- Version correctness depends on clean Git history and correct commit semantics.
- Developers must treat commit messages as part of the public API contract.

## Decision C4.2.2 — Script inference based on Unicode coverage

### Context

Fontshow needs a consistent and portable way to infer the writing systems
supported by a font, independently of platform-specific metadata and
language declarations.

Available inputs include:
- Unicode block usage statistics (FontConfig / fc-query)
- Unicode code point coverage (fontTools)

### Decision

Script inference is performed exclusively in `parse_font_inventory` using
Unicode coverage metadata and produces **ISO 15924** script codes.

The inference strategy follows a two-step approach:

1. **Primary source**: Unicode block statistics (`coverage.unicode_blocks`)
2. **Fallback**: Maximum Unicode code point (`coverage.unicode.max`)

All outputs are normalized to ISO 15924 codes and stored in
`fonts[].inference.scripts`.

If no reliable inference is possible, the value `["unknown"]` is emitted.

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

#### A. Branch Protection Rules with "Require signed commits"

- Result: ❌ CI commits rejected
- Reason: GitHub Actions cannot produce verified signatures

#### B. Repository Rulesets with signed-commit enforcement

- Result: ❌ Same limitation as above
- Rulesets correctly enforce signing, but do not distinguish CI-generated commits

#### C. GPG / SSH signing inside GitHub Actions

- Result: ❌ Not viable
- GitHub does not support associating CI-generated signatures
  with a verified GitHub identity

#### D. Forcing semantic-release to avoid commits

- Result: ⚠️ Partial
- Would require abandoning `@semantic-release/git`
- Incompatible with current release workflow

### Decision

The project adopts the following model:

- GitHub Repository Rulesets enforce commit signing
- Human-authored commits **must** be signed
- Trusted CI automation is granted a **documented bypass**
- GitHub remains the authoritative enforcement layer

This is the **only configuration that is both technically feasible
and auditable** with current GitHub capabilities.

### Consequences

- Local hooks are advisory, not authoritative
- CI automation is explicitly trusted and documented
- The policy may be revisited if GitHub adds support
  for verified CI signatures

## Decision status

The decisions listed in this document are to be considered **binding** for current project development.

Any changes to these decisions must be:
- explicitly discussed;
- reflected in this document;
- traceable through dedicated commits.
