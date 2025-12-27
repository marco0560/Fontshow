# Active Project Decisions

This document lists the **currently active project decisions** for Fontshow.

It does **not** include:
- historical background;
- discarded alternatives;
- past motivations.

For historical context and the evolution of decisions, refer to the **Development Diary**.

---

## Language and project structure

- **Python** is the primary language of the project.
- The project is structured as a **package**, not as a collection of standalone scripts.
- Module execution is preferably performed using:
  - `python -m <module>`

---

## Pipeline architecture

- The pipeline is divided into **independent stages**.
- Each stage has:
  - explicit inputs;
  - explicit outputs;
  - well-defined responsibilities.
- Intermediate artifacts (inventories, JSON files, LaTeX files) are considered an **integral part of the project**, not temporary by-products.

---

## Data handling

- Raw data is not modified or “cleaned” silently.
- Normalization:
  - does **not replace** original values;
  - adds normalized versions alongside the original data.
- The **Data Dictionary** is the normative reference for the meaning of data fields.

---

## Documentation

- Official project documentation is maintained using **MkDocs**.
- Markdown files under `docs/` constitute the **operational manual**.
- Automatically generated documentation based on code extraction is **not used**.
- The README and cheat-sheets are derived from the MkDocs documentation.

---

## Testing and quality

- Automated tests are based on **pytest**.
- Quality checks include linting and static validation tools.
- CI is considered the final authority on code quality.

---

## Work tracking and technical debt

- TODOs, bugs, and technical debt are tracked **exclusively via GitHub Issues**.
- Static TODO files in the repository are not used.
- Issues represent the operational state of the work.

---

## Development environment

- Development takes place in Linux and Linux-like environments (including WSL).
- Differences between environments are considered part of the problem domain.
- Validation on native Linux is considered necessary for critical functionality.

---

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

---

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

---

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

---

## Use coverage metrics without enforcement

**Decision**

Test coverage is measured using `pytest-cov`, but no minimum coverage
threshold is enforced at this stage.

**Rationale**

The project is still evolving and some modules interact with external
tools and environments that are difficult to test automatically.
Coverage metrics are used to guide testing efforts without slowing
development.

**Status**

Accepted

---

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

---

## Decision status

The decisions listed in this document are to be considered **binding** for current project development.

Any changes to these decisions must be:
- explicitly discussed;
- reflected in this document;
- traceable through dedicated commits.
