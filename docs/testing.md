# Testing

This document describes the testing strategy adopted in the Fontshow project.
It covers both automated tests (executed via Continuous Integration) and
manual or exploratory tests that require a real system environment.

As the project evolves, this document will be progressively extended to
cover:

- automated tests
- non-regression tests
- CI-based validation on commits or releases

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

---

### Scope of automated tests

The automated test suite currently covers:

- script inference (`infer_scripts`)
- language inference (`infer_languages`)
- validation of individual font entries (`validate_font_entry`)
- validation of complete inventories (`validate_inventory`)

These tests ensure the stability of Fontshow’s internal data contracts
and protect against regressions during refactoring.

---

### Running tests locally

To run the full automated test suite in a development environment:

```bash
pytest -q
```

The command must terminate without errors.

---

### Continuous Integration

The automated test suite is executed as part of the GitHub Actions
Continuous Integration pipeline.

On every push or pull request:

- the package is installed in editable mode
- code quality checks are enforced via `pre-commit`
- the full pytest test suite is executed

A failing automated test causes the CI pipeline to fail and prevents
documentation deployment.

---

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

---

## Repository cleanup

For development convenience, the repository provides a cleanup script
(`scripts/clean_repo.py`) to remove generated artifacts while preserving
the local virtual environment.

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

---

## Prerequisites

- Python virtual environment activated
- Fontshow executed from source
- At least one known font installed on the system
  (e.g. *DejaVu Sans*, *Liberation*, *Noto*)

Preliminary check:

```bash
python -m fontshow.create_catalog --help
```

The command must terminate without errors.

---

## Test case 1 — No `-T` option

### Command

```bash
python -m fontshow.create_catalog --list-test-fonts
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

### Notes

This test verifies that:

- no implicit filtering is applied
- the program does not crash when `-T` is absent

---

## Test case 2 — `-T` without argument (default test set)

### Command

```bash
python -m fontshow.create_catalog -T --list-test-fonts
```

### Expected behavior

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

---

## Test case 3 — `-T` with a single font

### Command

```bash
python -m fontshow.create_catalog -T "DejaVu Sans" --list-test-fonts
```

### Expected behavior

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

---

## Test case 4 — Multiple `-T` options

### Command

```bash
python -m fontshow.create_catalog \
  -T "DejaVu" \
  -T "Liberation" \
  --list-test-fonts
```

### Expected behavior

- `TEST_FONTS` contains all specified entries
- all installed fonts matching at least one entry are selected

### Expected output (structure)

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

---

## Test case 5 — Default + explicit test fonts

### Command

```bash
python -m fontshow.create_catalog \
  -T \
  -T "Liberation Mono" \
  --list-test-fonts
```

### Expected behavior

- `TEST_FONTS` is the union of:
  - the default test font set
  - explicitly specified font names
- selected fonts reflect this union

---

## Manual test: `--validate-inventory`

### Purpose

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

---

### Command

```bash
python -m fontshow.parse_font_inventory \
  font_inventory.json \
  --validate-inventory
```

---

### Expected behavior

- the inventory is parsed
- structural issues are reported as warnings or errors
- no output files are generated
- the program exits immediately after validation

---

### Notes on validation warnings and charset-only entries

When running inventory validation on inventories generated with
extended Fontconfig data (e.g. using `--include-fc-charset` in
`dump_fonts.py`), the inventory may contain entries that do not represent
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

---

## Cross-checks (all cases)

For every test case:

- the program terminates with exit code 0 (unless fatal structural errors are found)
- no LaTeX files are generated
- no output files are written
- the output is deterministic and ordered

---

## Success criteria

The test suite is considered **successful** if:

- all commands terminate without unexpected errors
- warnings are understandable and documented
- the output correctly reflects the inventory structure and configuration
- no unintended side effects are observed
