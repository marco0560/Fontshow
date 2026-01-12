# Environment Matrix

## Purpose and Scope

This document defines the execution environments in which Fontshow is known
to work reliably, partially, or experimentally.

Its purpose is **not** to guarantee universal compatibility, but to:

- make environmental assumptions explicit,
- support systematic debugging,
- clearly communicate support boundaries.

This document is especially relevant when diagnosing failures across
different operating systems, runtimes, or toolchains.

## Reference Environment (Baseline)

The reference environment for Fontshow is:

- Operating System: **Linux (native)**
- Font discovery: **fontconfig**
- LaTeX engine: **LuaLaTeX**
- TeX distribution: **TeX Live (full installation recommended)**
- Execution model:
  - font discovery
  - inventory generation
  - LaTeX generation
  - LaTeX compilation

All pipeline stages are expected to run **within the same environment**.

Any deviation from this baseline may result in partial or unexpected behavior.

## Supported Environments

| Environment                | Status                 | Notes                                                        |
|----------------------------|------------------------|--------------------------------------------------------------|
| Linux (native, bare metal) | Supported              | Baseline reference environment                               |
| Linux (container / chroot) | Supported with caveats | Font availability and fontconfig visibility must be verified |

## Partially Supported / Fragile Environments

| Environment                       | Status  | Known Issues                                                         |
|-----------------------------------|---------|----------------------------------------------------------------------|
| WSL (Windows Subsystem for Linux) | Fragile | Font discovery and LaTeX compilation may observe different font sets |
| Minimal TeX Live installations    | Fragile | Missing packages may prevent LuaLaTeX compilation                    |

## Experimental / Observed Environments

| Environment      | Status       | Notes                                                         |
|------------------|--------------|---------------------------------------------------------------|
| Windows (native) | Experimental | Different font discovery model; LaTeX toolchain not validated |

## CI Environment (GitHub Actions)

GitHub CI is **not** considered a full execution environment.

In CI, Fontshow is expected to support:

- linting
- validation
- packaging
- release automation

CI workflows do **not** execute LuaLaTeX and do not validate
end-to-end document generation.

## Common Failure Classes

Observed or anticipated failure classes include:

- Fonts discovered but not loadable by LuaLaTeX
- Mismatch between font discovery environment and compilation environment
- Missing system-level dependencies (fontconfig, TeX packages)
- Different font visibility between host OS and execution runtime
- Path or encoding issues across operating systems

## Debugging Guidance

When debugging Fontshow issues:

1. Identify the execution environment.
2. Compare it against the reference baseline.
3. Verify that font discovery and LaTeX compilation occur in the same environment.
4. Check system-level dependencies before inspecting application logic.
