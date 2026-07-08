# Decision 0034 - TeX Runtime Support and Distro Lag Policy

**Date**: 08/07/2026
**Status**: Accepted

## Context

Fontshow generates LaTeX catalogs from font inventories and relies on the local
LuaLaTeX, fontspec, luaotfload, Polyglossia, and TeX Live runtime to compile
the generated document.

Large catalogs can expose defects or limitations in older distro-packaged TeX
Live stacks even when the underlying problem has already been fixed upstream.
Debugging such failures can require specialist TeX knowledge and expensive
runtime tracing that is not reasonable to expect from casual Fontshow users.

Fontshow therefore needs a clear support boundary:

- upstream TeX maintainers should not be bothered about failures already fixed
  in current upstream releases
- Fontshow should not absorb responsibility for stale distro packages
- users need actionable diagnostics before a failure is classified

## Decision

Fontshow supports generation of deterministic LaTeX source and best-effort
catalog compilation against a sufficiently current TeX runtime.

The supported rendering contract is:

- Fontshow must emit valid, deterministic, diagnosable LaTeX for supported
  inventory inputs.
- Fontshow records the relevant LuaLaTeX runtime surface in inventory metadata,
  including the TeX Live release identifier when the engine reports one.
- PDF compilation failures are Fontshow defects only when the generated LaTeX
  is invalid or when a failure reproduces on a supported, current TeX runtime.
- Failures that occur only on stale distro-packaged TeX runtimes are treated as
  runtime packaging/version issues unless evidence shows that Fontshow emits
  invalid TeX.

For large catalogs, users should validate with a current upstream TeX Live
installation or another locally proven TeX runtime. Distro-packaged TeX Live
installations are supported on a best-effort basis unless they pass the
project's catalog smoke tests for the workload in question.

Known stale or problematic distro TeX packages may be documented as risky for
large catalogs. The first remediation for such failures is upgrading or
switching the TeX runtime, not opening an upstream TeX bug.

## Diagnostic Requirements

Bug reports for catalog compilation failures should include:

- the generated `.tex` file or a minimized reproducer
- the relevant inventory metadata
- `metadata.validation.lualatex.engine_version`
- `metadata.validation.lualatex.texlive_version`, when available
- `metadata.validation.lualatex.runtime_fingerprint`
- the LuaLaTeX log excerpt around the first fatal error
- whether the failure reproduces on current upstream TeX Live

Fontshow maintainers may ask for a smaller catalog or a current-runtime retry
before treating a rendering failure as an application defect.

## Consequences

- Fontshow does not promise universal compatibility with every distro TeX Live
  package.
- Large-catalog reliability is evaluated against observed runtime evidence,
  not only the presence of `lualatex` on `PATH`.
- Casual users are not expected to debug LuaTeX, fontspec, luaotfload, or
  Polyglossia internals.
- Upstream TeX maintainers should receive reports only for issues reproduced
  against current upstream releases or backed by strong evidence.
