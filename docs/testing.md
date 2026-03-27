# Testing

This document describes the testing strategy adopted in the Fontshow project.
It covers both automated tests (executed via Continuous Integration) and
manual or exploratory tests that require a real system environment.

As the project evolves, this document will be progressively extended to
cover:

- automated tests
- non-regression tests
- CI-based validation on commits or releases

## Validation Layers

Fontshow applies multiple layers of validation:

1. Structural validation
   - Enforced via JSON Schema
   - Required for catalog output

2. Semantic validation
   - Checks domain consistency
   - Emits warnings
   - Does not block catalog generation

This separation is intentional and reflects the variability of real-world font metadata.

## CLI tests and environment isolation

CLI-level tests under ``tests/cli/`` are designed to be **environment-independent**.

In particular, the ``preflight`` command performs checks that depend on the
runtime environment (e.g. LaTeX availability, CI constraints, system tools).
Executing the real preflight logic inside CLI tests would therefore make
those tests non-deterministic and environment-sensitive.

To avoid this, CLI tests **stub or monkeypatch the preflight execution path**
so that:

- no real environment checks are executed;
- the CLI output and exit code can be tested deterministically;
- behavior is identical across local development, WSL, CI, and native Linux.

This separation ensures that:

- environment-dependent behavior is tested in ``tests/preflight/``;
- CLI behavior (output, quiet mode, exit codes) is tested in isolation;
- end-to-end validation of the real pipeline is performed manually when needed
  on real host environments rather than through the deterministic pytest suite.

Such checks are intended for **manual, local execution only**.

They are:

- not executed in CI
- not required for normal development
- environment-specific and therefore intentionally separate from the required
  automated validation surface
- rewritten case-by-case when a concrete platform investigation is needed

They may assume the presence of system-specific tools, fonts, and
configurations.

In short:

```text
CLI tests do not test the environment.
CLI tests test the CLI.
```

## Gentoo validation: Fontconfig language codes vs ISO 639

During full pipeline testing on Gentoo Linux, the `fontshow validate-inventory` step
may emit a large number of `invalid_language_code` warnings.

This behavior is **expected** and **does not indicate a pipeline failure**.

### Root cause

Fontconfig exposes language tags that:

- are not guaranteed to be ISO 639 compliant
- may include:
  - region qualifiers (e.g. `ku-tr`, `zh-cn`)
  - legacy or deprecated codes (e.g. `mo`, `wen`)
  - script or source annotations (e.g. `bem(s)`, `lzh(s)`)

Fontshow currently preserves these tags verbatim in
`coverage.languages`, which is semantically correct but conflicts with
strict ISO 639 validation.

### Interpretation of warnings

- Warnings are **informational**
- Exit code remains `0`
- Inventory enrichment and downstream stages are unaffected

### Design note

A dual-field strategy has been approved:

- `coverage.languages_raw`: original Fontconfig language tags
- `coverage.languages`: normalized ISO 639 codes (lossy, validated)

This separation preserves raw data while allowing strict validation
and clean downstream processing.

See corresponding design decision [Decision 0013 - Language normalization strategy](`decisions/0013-language-normalization-strategy.md`).

## Language Inference Threshold Tests

### Scope and intent

The tests in `test_infer_languages_threshold.py` are designed to validate the
*language inference logic in isolation*, without involving font discovery,
FontConfig, or filesystem access.

In particular, these tests exercise:

- Unicode block coverage thresholds
- Language profile requirements (`required_blocks`)
- Regression safety for core Latin languages

### Important design constraint

The function `infer_languages()` operates **only on coverage-level data**.
It expects a `coverage` dictionary (as produced by the inventory pipeline),
*not* a full font entry and *not* a filesystem path.

As a consequence:

- Tests MUST pass only the `coverage` mapping
- Tests MUST NOT rely on real fonts or system-installed files
- Tests MUST NOT invoke FontConfig or font discovery logic

This keeps the tests deterministic, fast, and independent from the execution
environment.

### Threshold-based inference

Language inference is intentionally conservative.

A language is inferred only if:

1. All `required_blocks` are present in the coverage
2. Each required block exceeds a global coverage threshold
3. Symbolic or incidental block presence (e.g. a few codepoints) is ignored

For example:

- A small number of Greek codepoints does **not** imply Greek language support
- Substantial coverage of the *Greek and Coptic* block **does** imply Greek

### Rationale

This approach avoids false positives on:

- Pan-Unicode fonts
- Symbol fonts
- Utility or fallback fonts

and reflects real-world expectations for language support.

Any future refinement (e.g. per-block thresholds) must preserve this
conservative default behavior.

## Gentoo Linux — Fontconfig charset extraction

On native Gentoo Linux systems, charset extraction has been manually verified
with Fontshow and cross-checked against direct `fc-query` behavior.

Environment (example run):

- Fontconfig: 2.17.1
- Fontshow: 0.35.3.post3

Observed behavior:

- Direct `fc-query` (file-based):
  - TrueType fonts: `charset:` bitmap is present.
  - OpenType / Type1 / variable fonts: `fc-query` may fail with:
    `Can't query face 4294967295`.

- Direct `fc-query` (pattern-based `family:style=...`):
  - Charset extraction fails (not usable for this purpose).

- Fontshow `dump-fonts --include-fc-charset`:
  - `coverage.charset.raw` is populated (verified at scale: 5246/5246 fonts).
  - When `--include-fc-charset` is disabled, `coverage.charset` is absent.

Interpretation:

- Direct `fc-query` CLI behavior is not a reliable baseline for charset coverage.
- Fontshow can still capture and serialize Fontconfig charset bitmaps in practice
  even when direct `fc-query` fails for certain font types.

Current behavior:

- The Fontconfig charset bitmap is decoded into Unicode ranges during
  parse-inventory enrichment when charset data is available.
- Charset-derived fields may be attached under coverage:
  - `normalized_charset`
  - `unicode_blocks_from_charset`
  - `script_coverage_from_charset`
- Canonical `coverage.unicode_blocks` remains the authoritative source
  for script inference when present.
- Charset-derived script coverage is used as a secondary weighted signal
  and as fallback only when canonical block coverage is absent.
- When canonical and charset-derived coverage disagree, parse-inventory
  records structured diagnostics instead of silently reconciling them.

## Automated Tests (pytest)

Fontshow includes an automated test suite based on **pytest**.
These tests validate the internal data model and inference logic using
minimal, deterministic mock inputs.

Automated tests are designed to be:

- fast
- reproducible
- independent from the local font environment
- suitable for Continuous Integration (CI)

They do **not** rely on real font files, Fontconfig, or system-specific
configuration.

### Scope of automated tests

The automated test suite currently covers:

- script inference (`infer_scripts`)
- language inference (`infer_languages`)
- validation of individual font entries (`validate_font_entry`)
- validation of complete inventories (`validate_inventory`)

These tests ensure the stability of Fontshow’s internal data contracts
and protect against regressions during refactoring.

### Running tests locally

To run the full automated test suite in a development environment:

```bash
pytest -q
```

The command must terminate without errors.

### Continuous Integration

The automated test suite is executed as part of the GitHub Actions
Continuous Integration pipeline.

On every push or pull request:

- the package is installed in editable mode
- code quality checks are enforced via `pre-commit`
- the full pytest test suite is executed

A failing automated test causes the CI pipeline to fail and prevents
documentation deployment.

### Code coverage

Test coverage is measured using `pytest-cov`.

Coverage reports are generated during Continuous Integration to help
identify untested code paths and guide future test additions.

Coverage metrics are used to highlight untested code paths and guide
testing efforts. At this stage, no minimum coverage threshold is enforced
in order to preserve development velocity.

Generated artifacts such as `.coverage`, `coverage.xml`, and `htmlcov/`
are considered local and are not tracked in version control.

### Relationship with manual tests

Automated tests and manual tests serve **complementary purposes**:

- automated tests validate internal logic and data integrity
- manual tests validate real-world behavior, integration with external
  tools, and environment-specific scenarios

Manual test procedures are documented in the following sections.

## Manual and Exploratory Tests

Some aspects of Fontshow require manual testing, including:

- Font discovery via Fontconfig (`fc-list`, `fc-query`)
- Cross-platform behavior (Linux native vs WSL vs Windows)
- LaTeX compilation and font loading
- Rendering and visual inspection of generated catalogs

These tests depend on the local environment and available fonts and are
therefore not suitable for full automation.

## Repository cleanup

For development convenience, the repository provides a cleanup script
(`scripts/clean_repo.py`) to remove generated artifacts while preserving
the local virtual environment.

## Gentoo Linux – Test Environment

### System information

- **Distribution**: Gentoo Linux
- **Kernel**: Linux 6.12.58-gentoo-dist (PREEMPT_DYNAMIC)
- **Architecture**: x86_64
- **CPU**: Intel(R) Core(TM) i7-8700K @ 3.70GHz

### Python environment

- **Python version**: 3.13.9
- **Virtual environment**: enabled (`.venv`)

### Fontconfig

- `fontconfig` binary: **not present** in PATH
- `fc-list` version: **fontconfig 2.17.1**

> Note: despite the absence of a `fontconfig` executable, Fontconfig is correctly
> installed and accessible via `fc-list`.

### LuaLaTeX

- **Engine**: LuaHBTeX
- **Version**: 1.18.0
- **TeX distribution**: TeX Live 2024 (Gentoo Linux)

### Installed fonts

- The list of installed fonts was captured using:

  ```bash
  fc-list > lista_fonts_installati
  ```

- Resulting file: `lista_fonts_installati`
- The file was manually inspected and appears non-empty and consistent with
  the system font configuration.

## Preflight check

### Invocation attempt

The preflight check was invoked using:

```bash
fontshow preflight
```

### Observed behavior

- The command is implemented as a regular CLI subcommand and also has a
  dedicated module entrypoint via `python -m fontshow.preflight`.

### Outcome

- Preflight should execute normally and report runtime capability checks
  according to the current environment.
- No workaround was attempted at this stage
- Further investigation is deferred until after test documentation is completed

## dump_fonts and inventory processing (Gentoo)

### dump_fonts – basic invocation

The font discovery phase was executed using:

```bash
fontshow dump-fonts
```

#### dump_fonts Observed behavior

- The command completes successfully without errors.
- Execution time is **noticeably long**, due to the high number of installed fonts.
- During execution, **no progress indicator** is shown.
- This may give the impression that the process is stalled on systems with many fonts.

#### dump_fonts Notes

- A progress indicator existed in a previous version and would significantly
  improve usability in this scenario.
- This is an observation related to UX, not a functional failure.

### dump_fonts – output file and charset comparison

The command was executed again, explicitly specifying the output file:

```bash
fontshow dump-fonts -o font_inventory_with_charset.json
```

Resulting files:

- `font_inventory.json`
- `font_inventory_with_charset.json`

A diff between the two files shows:

```bash
diff font_inventory.json font_inventory_with_charset.json
```

#### with charset Observed behavior

- The only difference between the two files is the `generated_at` timestamp.
- No additional charset-related data appears in the output.

#### dump_fontsOutcome

- On this Gentoo system, enabling charset-related output does **not** modify
  the resulting inventory.
- Charset extraction appears to be ineffective or unavailable in this context.

## Inventory parsing and validation

### Inventory parsing

The inventory was parsed using:

```bash
fontshow parse-inventory font_inventory.json
```

#### Inventory parsing Observed behavior

- Parsing completes successfully.
- An enriched inventory file is generated:
  - `font_inventory_enriched.json`

### Inventory validation

Explicit validation was executed using:

```bash
fontshow parse-inventory --validate-inventory font_inventory.json
```

#### Inventory Validation Observed behavior

- Validation fails with a large number of errors.
- All reported errors follow the same pattern:

  - `path: None`
  - missing or invalid `path`
  - missing or invalid `family`
  - missing or invalid `style`

- Total invalid entries reported: **5526**

#### Inventory Validation Outcome

- The inventory generated by `dump_fonts` does **not** satisfy the validation
  constraints enforced by `--validate-inventory`.
- Despite this, the inventory remains usable by the pipeline (see below).

## Catalog generation pipeline

### Invocation

The catalog generation was executed using the unified module:

```bash
fontshow create-catalog
```

> Note: the previous script `crea_catalogo_pipeline_v2.py` has been replaced
> by the `create_catalog` module.

### Catalog generation Observed behavior

- The inventory is loaded successfully:
  - 5526 fonts detected
- A warning is emitted:
  - inventory schema_version `1.1` is not explicitly supported
- LaTeX generation proceeds without errors.

Progress output example:

```text
Generating LaTeX file for 3116 fonts...
  ... processed 500/3116
  ... processed 1000/3116
  ... processed 1500/3116
  ... processed 2000/3116
  ... processed 2500/3116
  ... processed 3000/3116
  ... processed 3116/3116
```

### Catalog generation Outcome

- A LaTeX file is generated successfully:
  - `fontshow_Linux_20260105_000.tex`
- The pipeline completes despite the inventory validation failures.
- Only a subset of fonts (3116 out of 5526) is actually processed for LaTeX output.

## Summary (Gentoo)

- `dump_fonts` works correctly but scales poorly in terms of perceived responsiveness.
- Charset extraction does not alter the inventory on this system.
- Inventory validation fails massively, yet:
  - parsing succeeds
  - catalog generation succeeds
- The pipeline is robust against incomplete or partially invalid inventory data.

---

## Windows 11 — Manual validation (Fontconfig / charset / catalog)

Environment (example run):

- OS: Windows 11
- Fontshow: 0.35.3.post6
- PowerShell: 7.5.4

### Charset extraction

Observed:

- `fontshow dump-fonts --include-fc-charset` produces **no charset data**:
  - Fonts discovered: 466
  - Fonts with `coverage.charset`: 0
- Behavior identical with and without `--include-fc-charset`.

Interpretation:

- Windows build does **not use Fontconfig**.
- Fontconfig charset information is therefore unavailable.
- `coverage.charset` remaining null is **expected behavior**.

---

### dump-fonts / parse-inventory

Observed:

- `dump-fonts` completes successfully.
- `parse-inventory` completes successfully.
- Deterministic output, no structural failures.

---

### Catalog generation (LuaLaTeX)

Observed:

- LaTeX file generated successfully.
- LuaLaTeX compilation completes without fatal errors.
- However, fonts are **not loaded correctly** by LuaLaTeX.

Example result:

- Fonts analyzed: 1
- Working fonts: 0
- Problematic fonts: 1
- Reported as: `Unknown Font → Non Caricato`

Interpretation:

- Windows font identity resolution is incomplete.
- This matches the known limitation tracked in **Issue #51**.
- Not a regression.

---

### Summary (Windows)

- Charset extraction: **unsupported on Windows**
- dump/parse pipeline: **stable**
- Catalog generation: **functional but limited by font identity**
- Reference: **Issue #51**

---

## WSL (Fedora 43) — Manual validation (Fontconfig / charset / catalog)

Environment (example run):

- Platform: WSL2 (Windows Subsystem for Linux)
- Kernel: 6.6.87.2-microsoft-standard-WSL2
- Fontconfig: 2.17.0
- Fontshow: 0.35.3.post6

### Charset extraction

Observed:

- Direct `fc-query` on font file fails:
  - Example: `Can't query face 4294967295`
- However, `fontshow dump-fonts --include-fc-charset` **successfully populates charset**:
  - Fonts discovered: 1295
  - Fonts with `coverage.charset`: 1295
- Without `--include-fc-charset`: 0 fonts contain charset.

Interpretation:

- Direct `fc-query` CLI is unreliable in this environment.
- Fontshow Fontconfig integration successfully extracts charset in practice.
- Behavior matches Gentoo in outcome (full charset coverage), though not in `fc-query` CLI behavior.

---

### dump-fonts / parse-inventory

Observed:

- `dump-fonts` completes successfully.
- `parse-inventory` completes successfully.
- Deterministic output, no structural failures.

---

### Catalog generation (LuaLaTeX)

Observed:

- LaTeX file generated successfully.
- No fatal errors during generation.
- Catalog generation is functional.

Notes:

- Some fonts report `"<unknown>" has no declared language coverage`.
- This does not affect generation and is informational.

---

### Summary (WSL Fedora 43)

- Charset extraction: **supported via Fontshow (not via direct fc-query)**
- dump/parse pipeline: **stable**
- Catalog generation: **functional**

## LuaLaTeX compilation (reduced font set, Gentoo)

### LuaLaTeX compilation Rationale

Compiling the full font catalog generated from the complete inventory
was observed to be **prohibitively slow** (several minutes).
For this reason, LaTeX compilation was tested on a **reduced subset of fonts**
generated using the `-T` option.

### Catalog generation (reduced set)

The catalog was generated using:

```bash
fontshow create-catalog -T
```

#### LuaLaTeX compilation Observed behavior

- Inventory loaded successfully:
  - 5526 fonts detected
- Warning emitted:
  - inventory schema_version `1.1` not explicitly supported
- LaTeX catalog generated for a reduced set:
  - **1283 fonts processed**

Progress output:

```text
Generating LaTeX file for 1283 fonts...
  ... processed 500/1283
  ... processed 1000/1283
  ... processed 1283/1283
```

Generated file:

- `fontshow_Linux_20260105_001.tex`

### LuaLaTeX compilation

Compilation was executed using:

```bash
lualatex -interaction=nonstopmode fontshow_Linux_20260105_001.tex > fontshow_Linux_20260105_001.log
```

#### LuaLaTeX Observed behavior

- Compilation completes, producing a `.log` file.
- Total compilation time is approximately **5 minutes**, even with a reduced font set.
- The resulting log file contains **a large number of errors**.

#### LuaLaTeX compilation Outcome

- LuaLaTeX compilation is **not clean** on Gentoo, even when using a reduced font subset.
- Errors are numerous and require further analysis.
- No attempt was made at this stage to classify or suppress errors.

#### Artifacts

- LaTeX source:
  - `fontshow_Linux_20260105_001.tex`
- Compilation log:
  - `fontshow_Linux_20260105_001.log`

## Notes on testing

- Using a reduced font set is currently necessary to make iterative testing feasible.
- Full catalog compilation is possible but not practical for routine testing.

## LuaLaTeX log analysis (Gentoo, reduced font set)

### Overview

The LuaLaTeX compilation log generated from a reduced font set
(`fontshow_Linux_20260105_001.log`) contains a large number of errors.
A closer inspection shows that these errors fall into a small number of
well-defined classes.

### Error class 1: polyglossia package errors

The log contains many repeated occurrences of the following error:

```text
! Package polyglossia Error: The current main roman font, lmroman10-regular,
```

#### Characteristics

- The error is emitted by the `polyglossia` package.
- It is **not tied to a specific catalog font**.
- The same error message is repeated many times.
- Compilation continues due to `-interaction=nonstopmode`.

#### Impact

- The log becomes very noisy.
- The error obscures font-specific issues.
- This appears to be a **global LaTeX configuration issue**, not a per-font failure.

### Error class 2: missing glyphs in non-Latin fonts

The log contains many warnings of the form:

```text
Missing character: There is no ö (U+00F6) in font name: AR PL KaitiM Big5
Missing character: There is no ä (U+00E4) in font name: NewCM08Devanagari
```

#### LuaLaTeX log Characteristics

- Affects CJK, Indic, and other non-Latin fonts.
- Missing glyphs correspond to Latin or Latin-1 characters.
- Errors are font-specific but expected given the script coverage.

#### LuaLaTeX log Impact

- These warnings are non-fatal.
- They indicate a lack of script-aware filtering during catalog generation.

### Error class 3: scale-related log amplification

- A large number of fonts (1283) are processed.
- Similar warnings and errors are repeated for many fonts.
- The resulting log is difficult to analyze manually.

### Summary

- LuaLaTeX compilation completes, but produces a large number of errors.
- Errors can be grouped into:
  - global LaTeX configuration issues
  - expected missing glyphs in non-Latin fonts
- Reduced font sets are required to make debugging feasible.

## Single-font case study: AR PL KaitiM Big5 (Gentoo)

### Font identification

The following entries were identified using Fontconfig:

```bash
fc-list | grep -F "AR PL KaitiM"
```

Result:

```text
/usr/share/fonts/arphicfonts/bkai00mp.ttf: AR PL KaitiM Big5,文鼎ＰＬ中楷:style=Regular
/usr/share/fonts/arphicfonts/gkai00mp.ttf: AR PL KaitiM GB,文鼎ＰＬ简中楷:style=Regular
/usr/share/texmf-dist/fonts/truetype/public/arphic-ttf/bkai00mp.ttf: AR PL KaitiM Big5,文鼎ＰＬ中楷:style=Regular
/usr/share/texmf-dist/fonts/truetype/public/arphic-ttf/gkai00mp.ttf: AR PL KaitiM GB,文鼎ＰＬ简中楷:style=Regular
```

### Observations

- Two regional variants are present:
  - **AR PL KaitiM Big5** (Traditional Chinese)
  - **AR PL KaitiM GB** (Simplified Chinese)
- Each variant is installed twice:
  - once as a system font
  - once as part of the TeX Live distribution

### Selected font for the case study

The following file was selected as the reference font for this case study:

- **Path**: `/usr/share/fonts/arphicfonts/bkai00mp.ttf`
- **Family**: AR PL KaitiM Big5
- **Style**: Regular

### File verification

```bash
ls -l /usr/share/fonts/arphicfonts/bkai00mp.ttf
```

```text
-rw-r--r-- 1 root root 10580352 Oct 30 15:08 /usr/share/fonts/arphicfonts/bkai00mp.ttf
```

```bash
file /usr/share/fonts/arphicfonts/bkai00mp.ttf
```

```text
TrueType Font data, 20 tables, 1st "FFTM"
```

### File verification Outcome

- The font file exists and is readable.
- The file is a valid TrueType font.
- The font is non-Latin and uses a Traditional Chinese character set.
- Multiple installations of the same font family are present on the system.

## Single-font catalog generation: AR PL KaitiM Big5 (Gentoo)

### Objective

This test isolates a **single non-Latin font** in order to:

- reproduce LuaLaTeX behavior in a controlled scenario
- distinguish font-specific issues from global pipeline or LaTeX configuration problems

### Inventory reduction

Starting from the enriched inventory, a reduced inventory containing
a single font entry was created.

```bash
jq '
  .fonts
  |= map(select(.path == "/usr/share/fonts/arphicfonts/bkai00mp.ttf"))
' font_inventory_enriched.json > font_inventory_single_kaitim.json
```

Verification:

```bash
jq '.fonts | length' font_inventory_single_kaitim.json
```

Result:

```text
1
```

### Catalog generation

The catalog was generated using the reduced inventory:

```bash
FONT_INVENTORY=font_inventory_single_kaitim.json \
fontshow create-catalog
```

#### Catalog Observed behavior

- The pipeline completes successfully.
- Exactly one font is processed.
- A LaTeX source file is generated.

### LuaLaTeX compilation parms

```bash
lualatex -interaction=nonstopmode fontshow_Linux_*.tex > fontshow_single_kaitim.log
```

#### LuaLaTeX compilation and log Outcome

- Compilation completes and produces a log file.
- Errors and warnings are analyzed separately.
- This setup provides a minimal and reproducible test case.

## Single-font catalog and LuaLaTeX compilation: AR PL KaitiM (Gentoo)

### Catalog generation using name-based filtering

A reduced catalog was generated using the built-in name filter:

```bash
fontshow create-catalog -T "AR PL KaitiM"
```

#### Catalog generation with filters Observed behavior

- Inventory loaded successfully:
  - 5526 fonts detected
- Name-based filtering selects **2 fonts**:
  - AR PL KaitiM Big5
  - AR PL KaitiM GB
- A LaTeX source file is generated successfully.

### LuaLaTeX compilation nonstop mode

```bash
lualatex -interaction=nonstopmode fontshow_Linux_20260105_000.tex > fontshow_Linux_20260105_000.log
```

#### Observed behavior nonstop mode

- Compilation completes without fatal errors.
- The log contains **only missing glyph warnings**.
- No `polyglossia`-related errors are present.
- No LuaTeX crashes or hard failures are observed.

Example warnings:

```text
Missing character: There is no ä (U+00E4) in font AR PL KaitiM Big5
Missing character: There is no ö (U+00F6) in font AR PL KaitiM GB
```

### Outcome nonstop mode

- The AR PL KaitiM fonts do **not** trigger LuaLaTeX crashes.
- Observed warnings are consistent with limited Latin coverage.
- The behavior is reproducible and limited to expected missing glyph messages.
- Name-based font filtering (`-T`) is effective for isolated testing.

## Script/language mismatch in badges and sample text (Gentoo)

### Observed issue

For non-Latin fonts, the generated catalog may display an **inconsistent** language
label in the badges and use a **sample text** that does not match the font script.

Example (from a catalog generated with `-T "AR PL KaitiM"`):

- `AR PL KaitiM Big5`: `SCRIPTS: HANI | LANG: DE | TYPE: TEXT`
- `AR PL KaitiM GB`: `SCRIPTS: JPAN | LANG: DE | TYPE: TEXT`

The sample text rendered for both fonts is a German pangram (e.g. "Victor jagt zwölf...").

### Impact of mismatch

- The selected sample language drives the sample text selection.
- When the sample text uses characters not covered by the font script,
  LuaLaTeX produces many cascading warnings (e.g. `Missing character: ...`).

### Reproduction

```bash
fontshow create-catalog -T "AR PL KaitiM"
lualatex -interaction=nonstopmode fontshow_Linux_20260105_000.tex > fontshow_Linux_20260105_000.log
```

### Notes on mismatch

- This appears to be caused by the language selection policy:
  inferred languages are present, but the chosen “primary” language does not
  reflect the font’s primary script.
- A script-aware language prioritization would reduce false mismatches and
  improve the relevance of sample text rendering.

## Manual test: `--list-test-fonts`

### Purpose

Verify the correct behavior of the CLI option:

```text
--list-test-fonts
```

The option must:

- display the effective content of the `TEST_FONTS` set
- display the **installed fonts** selected by `TEST_FONTS`
- terminate without generating LaTeX output

This option is intended as a **debug and inspection tool**.

## Prerequisites

- Python virtual environment activated
- Fontshow executed from source
- At least one known font installed on the system
  (e.g. *DejaVu Sans*, *Liberation*, *Noto*)

Preliminary check:

```bash
fontshow create-catalog --help
```

The command must terminate without errors.

## Test case 1 — No `-T` option

### Command

```bash
fontshow create-catalog --list-test-fonts
```

### Expected behavior

- `TEST_FONTS` is empty
- No installed fonts are selected

### Expected output (structure)

```text
TEST_FONTS configuration:
  (empty)

Installed fonts matching TEST_FONTS:
  (none)
```

### Notes on test case 1

This test verifies that:

- no implicit filtering is applied
- the program does not crash when `-T` is absent

## Test case 2 — `-T` without argument (default test set)

### Command Test case 2

```bash
fontshow create-catalog -T --list-test-fonts
```

### Expected behavior Test case 2

- `TEST_FONTS` contains the default test font set (`DEFAULT_TEST_FONTS`)
- if the default set is empty:
  - behavior is identical to Test case 1
- if the default set is populated in the future:
  - matching fonts are listed accordingly

### Expected output (default empty)

```text
TEST_FONTS configuration:
  (empty)

Installed fonts matching TEST_FONTS:
  (none)
```

## Test case 3 — `-T` with a single font

### Command Test case 3

```bash
fontshow create-catalog -T "DejaVu Sans" --list-test-fonts
```

### Expected behavior Test case 3

- `TEST_FONTS` contains one entry: `"DejaVu Sans"`
- if the font is installed:
  - it appears in the selected font list
- if the font is not installed:
  - no installed fonts are listed

### Expected output (font installed)

```text
TEST_FONTS configuration:
  - DejaVu Sans

Installed fonts matching TEST_FONTS:
  - DejaVu Sans
```

## Test case 4 — Multiple `-T` options

### Command Test case 4

```bash
fontshow create-catalog \
  -T "DejaVu" \
  -T "Liberation" \
  --list-test-fonts
```

### Expected behavior Test case 4

- `TEST_FONTS` contains all specified entries
- all installed fonts matching at least one entry are selected

### Expected output (structure) Test case 4

```text
TEST_FONTS configuration:
  - DejaVu
  - Liberation

Installed fonts matching TEST_FONTS:
  - DejaVu Sans
  - DejaVu Serif
  - Liberation Mono
  - Liberation Sans
```

(The exact list depends on the fonts installed on the system.)

## Test case 5 — Default + explicit test fonts

### Command Test case 5

```bash
fontshow create-catalog \
  -T \
  -T "Liberation Mono" \
  --list-test-fonts
```

### Expected behavior Test case 5

- `TEST_FONTS` is the union of:
  - the default test font set
  - explicitly specified font names
- selected fonts reflect this union

## Manual test: `--validate-inventory`

### Purpose Test case 5

Verify the structural integrity of a Fontshow font inventory without
generating output or modifying data.

The option:

```text
--validate-inventory
```

performs a **soft validation** of the inventory JSON structure and exits.

It is intended for:

- debugging
- diagnostics
- CI or pre-processing checks

### Command Test case 5-2

```bash
fontshow parse-inventory \
  font_inventory.json \
  --validate-inventory
```

### Expected behavior Test case 5-2

- the inventory is parsed
- structural issues are reported as warnings or errors
- no output files are generated
- the program exits immediately after validation

### Notes on validation warnings and charset-only entries

When running inventory validation on inventories generated with
extended Fontconfig data (e.g. using `--include-fc-charset` in
`fontshow dump-fonts`), the inventory may contain entries that do not represent
individual fonts but rather Unicode charset information.

Such entries typically lack both:

- `identity.family`
- `base_names`

During validation, these entries may trigger warnings of the form:

```text
Warning: font entry #N has no family or base_names
```

These warnings are **informational** and do not indicate an invalid
inventory. Charset-only entries are preserved intentionally but are not
selectable for catalog generation or test font filtering.

## Cross-checks (all cases)

For every test case:

- the program terminates with exit code 0 (unless fatal structural errors are found)
- no LaTeX files are generated
- no output files are written
- the output is deterministic and ordered

## Success criteria

The test suite is considered **successful** if:

- all commands terminate without unexpected errors
- warnings are understandable and documented
- the output correctly reflects the inventory structure and configuration
- no unintended side effects are observed
