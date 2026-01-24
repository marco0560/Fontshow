# Lessons Learned

> ⚠️ **Engineering Notes – Non-Normative Document**
>
> This document collects *lessons learned* during development.
> It reflects reasoning, mistakes, and decisions observed over time.
>
> It is **not** a specification, **not** a contract, and **not** a source of truth
> for system behavior.
>
> Its purpose is to:
>
> - preserve engineering context
> - document recurring pitfalls
> - support future design decisions
> - reduce cognitive load when revisiting past work
>
> The contents may evolve, be refined, or become obsolete as the project evolves.

## Table of Contents

<!-- toc -->
- [Lessons Learned](#lessons-learned)
- [Table of Contents](#table-of-contents)
- [Scope](#scope)
- [1. Process & Decision Making](#1-process--decision-making)
- [L0001 – Context must be explicit](#l0001--context-must-be-explicit)
- [L0002 – Decisions must precede implementation](#l0002--decisions-must-precede-implementation)
- [L0003 – Structure must exist before automation](#l0003--structure-must-exist-before-automation)
- [L0004 – Small steps outperform large refactors](#l0004--small-steps-outperform-large-refactors)
- [2. Documentation as a System Component](#2-documentation-as-a-system-component)
- [L0010 – Documentation is part of the architecture](#l0010--documentation-is-part-of-the-architecture)
- [L0011 – Decisions require lifecycle management](#l0011--decisions-require-lifecycle-management)
- [L0012 – Documentation must match reality](#l0012--documentation-must-match-reality)
- [3. Tooling & Automation](#3-tooling--automation)
- [L0020 – Tooling is production code](#l0020--tooling-is-production-code)
- [L0021 – Automation must be explicit](#l0021--automation-must-be-explicit)
- [L0022 – CI is an architectural validator](#l0022--ci-is-an-architectural-validator)
- [4. API, CLI, and Interface Design](#4-api-cli-and-interface-design)
- [L0030 – Contracts must be explicit](#l0030--contracts-must-be-explicit)
- [L0031 – CLI output has semantic layers](#l0031--cli-output-has-semantic-layers)
- [L0032 – Quiet and verbose modes must be strict](#l0032--quiet-and-verbose-modes-must-be-strict)
- [L0033 – CLI logic must be testable](#l0033--cli-logic-must-be-testable)
- [L0034 – CLI behavior must follow platform conventions](#l0034--cli-behavior-must-follow-platform-conventions)
- [5. Architecture & Code Structure](#5-architecture--code-structure)
- [L0040 – Separation of concerns must be enforced](#l0040--separation-of-concerns-must-be-enforced)
- [L0041 – Registries are catalogs, not execution plans](#l0041--registries-are-catalogs-not-execution-plans)
- [L0042 – Schema evolution must be explicit](#l0042--schema-evolution-must-be-explicit)
- [6. Testing & Validation](#6-testing--validation)
- [L0050 – Tests must validate intent, not implementation](#l0050--tests-must-validate-intent-not-implementation)
- [L0051 – Coverage is a signal, not a goal](#l0051--coverage-is-a-signal-not-a-goal)
- [L0052 – Integration paths should not be unit-tested aggressively](#l0052--integration-paths-should-not-be-unit-tested-aggressively)
- [L0053 – Tests expose architectural flaws early](#l0053--tests-expose-architectural-flaws-early)
- [L0054 – Tests must not depend on environment state](#l0054--tests-must-not-depend-on-environment-state)
- [L0055 – Failing tests are more valuable than passing ones](#l0055--failing-tests-are-more-valuable-than-passing-ones)
- [7. Logging & Observability](#7-logging--observability)
- [L0060 – Logging must be designed, not improvised](#l0060--logging-must-be-designed-not-improvised)
- [L0061 – Log levels must have strict meaning](#l0061--log-levels-must-have-strict-meaning)
- [L0062 – Observability beats guesswork](#l0062--observability-beats-guesswork)
- [L0063 – Debugging requires control, not intuition](#l0063--debugging-requires-control-not-intuition)
- [8. Versioning & Release Discipline](#8-versioning--release-discipline)
- [L0070 – Version must have a single source of truth](#l0070--version-must-have-a-single-source-of-truth)
- [L0071 – CI is authoritative for releases](#l0071--ci-is-authoritative-for-releases)
- [L0072 – Security rules must be documented](#l0072--security-rules-must-be-documented)
- [9. Process-Level Principles](#9-process-level-principles)
- [L0080 – Assumptions are liabilities](#l0080--assumptions-are-liabilities)
- [L0081 – Not fixing something can be correct](#l0081--not-fixing-something-can-be-correct)
- [L0082 – Decisions reduce cognitive load](#l0082--decisions-reduce-cognitive-load)
- [10. Core Principles](#10-core-principles)
- [L0090 – Structure before automation](#l0090--structure-before-automation)
- [L0091 – Documentation before tooling](#l0091--documentation-before-tooling)
- [L0092 – Decisions before code](#l0092--decisions-before-code)
- [End of Document](#end-of-document)
<!-- tocstop -->

## Scope

This document captures **generalized, transferable lessons** derived from real development and debugging sessions.

All project-specific details have been removed.
The focus is on **engineering practice**, not on a specific codebase.

---

## 1. Process & Decision Making

---

### L0001 – Context must be explicit

Implicit assumptions cause more failures than incorrect code.

Clear definition of:

- scope
- constraints
- goals
- non-goals

is required before any technical work begins.

---

### L0002 – Decisions must precede implementation

Writing code before documenting decisions leads to:

- scope creep
- accidental redesigns
- inconsistent behavior

A written decision acts as a **constraint**, not bureaucracy.

---

### L0003 – Structure must exist before automation

Automation applied to an undefined structure creates fragile systems.

Correct order:

- define structure
- validate assumptions
- document decisions
- automate

---

### L0004 – Small steps outperform large refactors

Incremental changes:

- are easier to validate
- reduce regression risk
- preserve intent

Large refactors without checkpoints increase uncertainty.

---

## 2. Documentation as a System Component

---

### L0010 – Documentation is part of the architecture

Documentation defines:

- intent
- boundaries
- invariants
- evolution constraints

If documentation diverges from behavior, the system becomes unstable.

---

### L0011 – Decisions require lifecycle management

Decision records must be:

- versioned
- append-only
- individually addressable
- traceable over time

Single monolithic documents do not scale.

---

### L0012 – Documentation must match reality

If behavior changes, documentation must change in the same commit.

Outdated documentation is a form of technical debt.

---

## 3. Tooling & Automation

---

### L0020 – Tooling is production code

Developer tooling must be:

- versioned
- reviewed
- deterministic
- documented

Temporary scripts almost never remain temporary.

---

### L0021 – Automation must be explicit

Implicit automation leads to:

- hidden dependencies
- irreproducible builds
- fragile workflows

Automation must declare:

- inputs
- outputs
- failure modes

---

### L0022 – CI is an architectural validator

CI failures often indicate:

- design inconsistencies
- missing contracts
- undocumented assumptions

CI is feedback on architecture, not just correctness.

---

## 4. API, CLI, and Interface Design

---

### L0030 – Contracts must be explicit

If behavior is not defined, each component invents its own rules.

This applies to:

- CLI flags
- return codes
- logging behavior
- configuration semantics

---

### L0031 – CLI output has semantic layers

Output must be classified as:

- user-facing output
- diagnostic information
- debug/trace data
- errors

Mixing these layers makes behavior untestable.

---

### L0032 – Quiet and verbose modes must be strict

Rules:

- quiet → no output except errors
- verbose → additive only
- no behavioral change based on verbosity

Anything else creates ambiguity.

---

### L0033 – CLI logic must be testable

CLI implementations should:

- separate parsing from execution
- avoid `sys.exit()` in business logic
- return structured results

Testability must be designed, not patched later.

---

### L0034 – CLI behavior must follow platform conventions

CLI behavior must follow established platform conventions, including:

- separation of stdout and stderr
- exit code semantics
- argument parsing rules
- error reporting conventions

Violating these expectations leads to fragile tests and user confusion.

Flags such as `--quiet` must only affect informational output and must not
suppress errors or diagnostics emitted by the runtime or argument parser.

---

## 5. Architecture & Code Structure

---

### L0040 – Separation of concerns must be enforced

Logic, orchestration, I/O, and diagnostics must not be mixed.

Each layer must have a single responsibility.

---

### L0041 – Registries are catalogs, not execution plans

A registry describes what exists.

Execution must be:

- explicit
- filtered
- intentional

Never assume that everything registered must run.

---

### L0042 – Schema evolution must be explicit

Schemas must:

- declare versions
- evolve intentionally
- never infer structure implicitly

Schema versioning is part of API stability.

---

## 6. Testing & Validation

---

### L0050 – Tests must validate intent, not implementation

Good tests:

- verify observable behavior
- assert contracts
- survive refactors

Bad tests:

- mirror internal structure
- depend on private state
- break on redesign

---

### L0051 – Coverage is a signal, not a goal

High coverage does not imply correctness.

Coverage must be interpreted:

- per module
- by responsibility
- in context

---

### L0052 – Integration paths should not be unit-tested aggressively

I/O-heavy or environment-dependent code should be validated via:

- integration checks
- preflight validation
- controlled manual verification

Not everything should be unit-tested.

---

### L0053 – Tests expose architectural flaws early

Many design issues emerge only when writing tests.

Tests act as a design feedback mechanism.

---

### L0054 – Tests must not depend on environment state

Tests depending on:

- filesystem layout
- installed tools
- OS-specific behavior

are not reliable unit tests.

---

### L0055 – Failing tests are more valuable than passing ones

A failing test often reveals:

- incorrect assumptions
- undocumented behavior
- mismatched expectations
- hidden coupling between components

Test failures should trigger a review of intent before any code change.
They frequently expose design issues rather than implementation bugs.

---

## 7. Logging & Observability

---

### L0060 – Logging must be designed, not improvised

Logging should be:

- structured
- centralized
- predictable

Ad-hoc logging creates noise and instability.

---

### L0061 – Log levels must have strict meaning

Each level must correspond to a specific intent.

If TRACE exists, it must be explicitly enabled.

---

### L0062 – Observability beats guesswork

Systems should expose:

- decision points
- intermediate state
- failure context

Debugging without visibility leads to speculation.

---

### L0063 – Debugging requires control, not intuition

Effective debugging requires:

- deterministic reproduction
- explicit breakpoints
- controlled execution flow
- observable state transitions

Guesswork and ad-hoc logging are poor substitutes for structured inspection.
Debugging tools should support reasoning, not replace it.

---

## 8. Versioning & Release Discipline

---

### L0070 – Version must have a single source of truth

Version information must come from:

- tags
- release metadata

Never from duplicated constants.

---

### L0071 – CI is authoritative for releases

Local environments must not control:

- version numbers
- releases
- publication logic

---

### L0072 – Security rules must be documented

Security behavior must be:

- explicit
- documented
- enforced by tooling

Implicit security assumptions always fail over time.

---

## 9. Process-Level Principles

---

### L0080 – Assumptions are liabilities

Every assumption must be:

- stated
- verified
- documented

Unstated assumptions accumulate risk.

---

### L0081 – Not fixing something can be correct

Fixing the wrong thing causes more damage than leaving it unchanged.

Restraint is an engineering skill.

---

### L0082 – Decisions reduce cognitive load

Writing decisions:

- prevents repeated debates
- preserves rationale
- accelerates future work

---

## 10. Core Principles

---

### L0090 – Structure before automation

---

### L0091 – Documentation before tooling

---

### L0092 – Decisions before code

These principles prevent most long-term failures.

---

## End of Document
