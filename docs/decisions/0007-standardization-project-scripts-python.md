# Decision 0007 - Standardization of project scripts in Python

Date: 16/01/2026
Status: Accepted

## Context

The Fontshow repository historically contained a mix of helper scripts
implemented in different languages, primarily Bash (`.sh`) and Python.

These scripts served various purposes, including:

- repository cleanup and maintenance
- release preview and local semantic-release checks
- generation of documentation artifacts
- local, platform-specific end-to-end testing helpers

While functional, the Bash-based scripts introduced several issues:

- limited portability across platforms (Linux, macOS, Windows, WSL)
- inconsistent error handling and exit code semantics
- reliance on shell-specific features and environments
- increased maintenance cost and cognitive load
- friction when integrating with Git aliases and argument forwarding

At the same time, the project already relies heavily on Python, both for
production code and for tooling (tests, CI helpers, documentation generation).

## Decision

All project helper scripts are standardized on **Python**.

Specifically:

- Existing Bash scripts are replaced with equivalent Python scripts.
- New helper scripts MUST be implemented in Python.
- Scripts are placed under the `scripts/` directory.
- Scripts rely only on the Python standard library unless there is a
  compelling reason to introduce external dependencies.

Git aliases are used as the primary user-facing entrypoints for these scripts,
with arguments transparently forwarded to the underlying Python implementation.

Examples include:

- `git clean-repo`
- `git new-decision`
- `git gen-issues`
- `git gen-miles`

Some scripts (e.g. Gentoo-style end-to-end tests) are explicitly designated
as **local helpers** and are not intended to be used in CI pipelines.

## Consequences

### Positive

- Improved cross-platform compatibility.
- Consistent error handling and exit code semantics.
- Reduced reliance on shell-specific behavior.
- Easier maintenance and refactoring.
- Clearer mental model for contributors.
- Better integration with Git aliases and tooling.

### Neutral / Trade-offs

- Slightly more verbose implementations compared to small Bash scripts.
- Contributors need basic familiarity with Python (already a project
  requirement).

### Non-goals

- No change to CI behavior or pipelines as a result of this decision.
- No introduction of new runtime dependencies.
- No requirement to retroactively rewrite scripts that are no longer used.

This decision establishes a clear and maintainable direction for project
tooling, aligned with the existing architecture and long-term sustainability
of the Fontshow codebase.
