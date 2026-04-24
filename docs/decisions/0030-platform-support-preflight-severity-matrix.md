# Decision 0030 - Platform Support and Preflight Severity Matrix

**Date**: 24/04/2026
**Status**: Accepted

## Context

The repository already enforces a platform support matrix in preflight code
and tests, but no active decision record explicitly owns that contract.

Evidence:

- `src/fontshow/preflight/checks/environment.py:127-129` states that Linux
  bare-metal is the fully supported baseline, Linux non-bare-metal and Windows
  return warnings, and other operating systems return errors.
- `tests/preflight/test_environment_matrix.py:34-42` verifies Linux
  bare-metal as `OK`, Linux WSL/container/CI as `WARN`, Windows as `WARN`,
  and macOS as `ERROR`.
- `src/fontshow/preflight/checks/font_discovery.py:81-83` states that Linux
  requires `fc-list` unless execution is classified as CI, Windows reports
  limited support, and unsupported platforms return an error.
- `tests/preflight/test_latex_policy.py:40-43` verifies LuaLaTeX severity
  across Linux CI, Windows, and macOS.

## Decision

Fontshow adopts the preflight platform severity matrix already enforced by
the repository:

- Linux bare-metal is the primary supported runtime and should report `OK`
  when required capabilities are present.
- Linux WSL, Linux containers, and Linux CI are supported with warnings where
  environment constraints may affect font discovery or rendering.
- Windows is supported with limited/experimental status and should report
  warnings when capabilities are present but portability constraints remain.
- Unsupported operating systems, including macOS in the current contract,
  report errors.
- CI may downgrade or skip host-dependent discovery checks when the check is
  explicitly designed to avoid reliance on host font state.

Preflight tests are the authoritative executable contract for this matrix.
Any change to platform support level or severity classification requires an
ADR update and matching tests.

## Consequences

- Platform support is no longer only implicit in preflight implementation.
- Preflight behavior changes that affect portability are architectural changes.
- Windows remains warning-level unless a future ADR promotes it to full
  support.
- macOS remains unsupported until an ADR and tests define support behavior.
- CI behavior remains allowed to differ from local host behavior when the
  difference is explicit and tested.
