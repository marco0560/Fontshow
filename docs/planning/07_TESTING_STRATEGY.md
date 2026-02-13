# TESTING_STRATEGY.md

## Fontshow — Testing Strategy and Coverage Policy

**Current version:** v0.28.7.post14
**Applies to:** All tests and CI executions after base-zero planning

---

## Purpose

This document defines the **testing philosophy**, **test categorization**,
and **coverage expectations** for the Fontshow project.

Its goals are:

- deterministic test behavior across environments,
- clear separation of responsibilities between test types,
- meaningful coverage metrics,
- predictable CI execution.

This document is **normative**.

---

## Guiding Principles

- **Determinism first**
  Tests must produce the same result regardless of environment,
  unless explicitly marked otherwise.

- **Explicit environment dependence**
  Any test relying on external tools, fonts, or system configuration
  must be clearly identified and isolated.

- **Coverage as a contract**
  Coverage metrics exist to enforce guarantees, not to chase percentages.

---

## Test Categories

### Unit Tests

#### Unit Tests Definition

- Test pure logic and data transformations.
- Must not depend on filesystem layout, FontConfig, LaTeX, or OS-specific tools.

#### Unit Tests Characteristics

- Fast
- Deterministic
- Runnable on any platform

#### Unit Tests Examples

- Language inference logic
- Data normalization functions
- Schema validation helpers

---

### Integration Tests

#### Integration Tests Definition

- Test interaction with external systems or tools.
- May depend on:
  - filesystem,
  - FontConfig,
  - LaTeX,
  - OS-level capabilities.

#### Integration Tests Characteristics

- Potentially slower
- Explicitly environment-dependent
- May be skipped or marked in CI

#### Integration Tests Examples

- Catalog generation using real fonts
- LaTeX PDF rendering
- End-to-end CLI execution with system tools

---

## Test Marking and Organization

- Tests MUST be explicitly marked (e.g. `@pytest.mark.unit`, `@pytest.mark.integration`).
- Default test runs MUST execute unit tests only.
- Integration tests MUST be opt-in.

Directory structure SHOULD reflect intent, but markers are authoritative.

---

## CI Policy

### Default CI Behavior

- Run all unit tests.
- Enforce coverage thresholds on unit tests only.
- Skip integration tests unless explicitly enabled.

### Optional CI Jobs

- Integration test jobs MAY exist.
- Failures in optional jobs MUST NOT block unrelated development.

---

## Coverage Policy

- Coverage thresholds apply to:
  - unit tests,
  - deterministic code paths only.

- Integration tests:
  - contribute to confidence,
  - but do not count toward coverage thresholds.

Coverage reports MUST clearly distinguish:

- covered vs uncovered code,
- deterministic vs environment-dependent paths.

---

## Anti-Patterns

The following are explicitly discouraged:

- Mixing unit and integration behavior in the same test.
- Writing tests that silently skip behavior without explanation.
- Relying on local developer environments for CI success.

---

## Change Policy

Changes to this strategy:

- require explicit documentation,
- must not invalidate existing guarantees silently.

Historical versions of this document must remain accessible.

---

## Determinism and Environment-Dependent Validation

As the project evolves toward a hardened and reproducible core, the testing strategy distinguishes between deterministic behavior and environment-dependent validation.

### Deterministic Behavior

For a given:

- system configuration,
- font set,
- LuaLaTeX runtime,
- and inventory input,

the system must produce reproducible results. Tests should ensure that:

- inventory generation is deterministic,
- catalog generation is reproducible,
- persisted loadability decisions remain stable when the runtime fingerprint matches,
- no unexpected variation occurs across repeated runs in the same environment.

These tests focus on stability and repeatability rather than functional correctness alone.

### Environment-Dependent Validation

Certain behaviors depend on the runtime environment, particularly LuaLaTeX font loadability. These validations:

- confirm whether fonts discovered by the system are actually loadable by the rendering engine,
- may vary across environments,
- are not purely deterministic across different systems.

Testing strategy must therefore:

- clearly separate deterministic tests from environment-dependent validation,
- allow environment-dependent checks to be executed when the required runtime is available,
- avoid treating environment variability as a functional failure of the system.

### Catalog Robustness Guarantees

Testing must verify that catalog generation:

- does not abort due to subset-empty conditions,
- does not abort due to fragile name-based font loading,
- behaves deterministically when loadability persistence is valid,
- safely falls back to runtime validation when persisted loadability becomes invalid.

### Role in Stabilization

These validations support the stabilization baseline by ensuring:

- rendering failures are eliminated,
- loadability persistence remains trustworthy,
- behavior is reproducible in a stable environment.

They form part of the criteria used to determine readiness for subsequent architectural transitions.

## Status

This testing strategy is **active** and mandatory for all new
tests and test refactors following v0.28.7.post14.
