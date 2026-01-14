# Decision 0003 — Python and Node.js Coexistence Strategy

## Status

**Status:** Accepted
**Date:** 2026-01-14

## Context

Fontshow uses both Python tooling (core library, CLI, tests) and Node.js
tooling (semantic-release, commit linting, local developer automation).

The introduction of Node.js tooling creates a `node_modules/` directory at
repository root level, which may interfere with Python packaging tools
using automatic package discovery (setuptools).

## Decision

The repository will continue to host both Python and Node.js tooling in a
single top-level workspace.

To prevent interference between ecosystems:

- Python packaging configuration MUST explicitly restrict package discovery
  to the `fontshow` package.
- `node_modules/` MUST remain excluded from Python package discovery.
- Node.js tooling is considered *development-only* and must not affect
  runtime Python distribution.

This decision avoids repository fragmentation while maintaining deterministic
Python builds.

## Consequences

- Editable installs (`pip install -e .`) and CI builds remain stable.
- Python and Node.js tooling can evolve independently.
- Repository structure remains simple and developer-friendly.
