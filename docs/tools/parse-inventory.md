# parse-inventory

This module enriches the raw font inventory produced by `dump_fonts`
by performing script, language, and writing-system inference.

It operates purely on JSON data and never inspects font binaries.

---

## Responsibilities

- Infer primary script(s)
- Infer language coverage
- Normalize Unicode coverage information
- Attach inference metadata to each font entry

---

## Scope and non-responsibilities

The `parse-inventory` stage is responsible for validating and normalizing
inventory data produced by earlier stages.

It is **not** responsible for:

- discovering fonts on the system
- inspecting font files directly
- extracting raw font metadata
- generating output artifacts
- performing LaTeX compilation

All font discovery and metadata extraction are performed upstream by
the dump stage.

All output generation is handled by the catalog generation stage.

This separation ensures that:

- parsing remains deterministic
- validation rules are centralized
- pipeline stages remain loosely coupled

---

## Inspection Mode

`parse-inventory` also provides a lightweight reporting mode for
already-generated inventories:

```bash
fontshow parse-inventory --list-missing-language-coverage
```

This mode:

- reads the selected inventory file,
- lists fonts whose `coverage.languages` field is empty,
- exits without writing an output file.

Output is deterministic and preserves inventory order.

## Loadability Jobs

`parse-inventory` refreshes LuaLaTeX render-loadability metadata for the
current TeX/fontspec/luaotfload/polyglossia setup. It can run multiple
render-loadability batches in parallel:

```bash
fontshow parse-inventory --loadability-jobs 8
```

The default is `4`. Use `1` for fully serial probing. Higher values can
reduce wall-clock time for large inventories, but they also increase CPU
load and may expose TeX cache contention on some systems.

## Structured warnings

Fontshow uses **structured warnings** to report non-fatal issues detected
during inventory parsing, validation, and inference.

Warnings are designed to be:

- deterministic
- machine-readable
- attached directly to the relevant inventory node

No warning affects inference results.

---

### Warning model

Warnings are represented as dictionaries with the following structure:

```json
{
  "code": "missing_declared_languages",
  "message": "No declared languages available from FontConfig; inference.languages will be derived solely from Unicode data",
  "severity": "info"
}
```

Each warning has:

- **code**
  A stable, machine-readable identifier suitable for filtering or tooling.

- **message**
  A human-readable description intended for end users.

- **severity**
  A qualitative severity level. Current values include:
  - `"info"`
  - `"warning"`
  - `"error"` (reserved for future use)

---

### Warning attachment

Warnings are attached directly to the inventory node they refer to:

- **Inventory-level warnings**
  Attached to the inventory root object (e.g. schema issues).

- **Font-level warnings**
  Attached to individual font entries (e.g. missing declared metadata).

Example:

```json
{
  "fonts": [
    {
      "path": "...",
      "warnings": [
        {
          "code": "missing_declared_languages",
          "message": "No declared languages available from FontConfig; inference.languages will be derived solely from Unicode data",
          "severity": "info"
        }
      ]
    }
  ]
}
```

---

### Warning API

All warnings are created using a single canonical API:

```python
add_structured_warning(
    target: dict,
    *,
    code: str,
    message: str,
    severity: str = "warning",
) -> None
```

Where:

- `target` is either the inventory root dictionary or a single font entry
- the target dictionary is modified **in place**

This API replaces earlier ad-hoc helpers and ensures a consistent and
unambiguous warning model across the entire codebase.

---

### Semantic validation of language codes

In addition to JSON Schema validation, Fontshow provides semantic checks
to ensure that all declared and inferred language codes are valid ISO 639
identifiers.

This validation step detects issues that cannot be expressed in JSON Schema,
such as invalid or mistyped language codes.

The following sources are checked:

- `coverage.languages` (declared languages)
- `inference.languages` (inferred languages)

Semantic validation is performed by the `fontshow validate-inventory` command and
emits structured warnings without failing the validation process.

---

## Language normalization and validation

This section documents how `parse-inventory` handles language data extracted
from font metadata.

Language processing is intentionally split into two independent stages:

- **normalization**
- **validation**

These stages affect behavior but do **not** change the inventory schema.

---

### Language normalization

Normalization is a best-effort transformation applied to language tags in order
to improve consistency across heterogeneous font metadata.

Normalization MAY include:

- canonical casing (e.g. `en-us` → `en-US`)
- replacement of deprecated subtags
- removal of unsupported private extensions
- mapping of legacy identifiers where possible

Normalization:

- does not guarantee correctness
- does not enforce standards
- does not fail processing

Its purpose is to reduce noise while preserving information.

---

### Validation modes

`parse-inventory` supports two validation modes.

#### Permissive mode (default)

- Invalid or deprecated language tags are accepted
- Warnings may be emitted
- Processing continues
- Normalized values may be produced

This mode prioritizes compatibility with real-world font metadata.

---

#### Strict mode (`--strict-bcp47`)

When enabled:

<!-- cheatsheet:start -->
- Only RFC-compliant BCP-47 language tags are accepted
- Deprecated or malformed tags cause a hard failure
- No silent normalization is applied
- Inventory generation stops on first violation
<!-- cheatsheet:end -->

Strict mode:

- affects validation only
- does not alter schema structure
- does not change output layout

---

## CLI Notes

Common parse-inventory usage patterns:

```bash
# Enrich the raw inventory
fontshow parse-inventory

# Validate an enriched inventory only
fontshow parse-inventory -I

# List fonts missing declared language coverage
fontshow parse-inventory --list-missing-language-coverage

# Enforce strict BCP-47 validation while enriching
fontshow parse-inventory --strict-bcp47
```

---

### Design principles

- Normalization ≠ validation
- Validation ≠ enforcement
- Enforcement is always explicit
- Behavior is deterministic and observable

---

### Non-goals

- Automatic language inference
- Linguistic correctness guarantees
- Silent mutation of source metadata

---

### Design notes

- Warnings are **informational only** and never block processing.
- Declared metadata is never modified based on warnings.
- The warning system is intentionally minimal and extensible.
- Wrapper functions for warning emission were removed in C4.3 to avoid
  ambiguity and duplicated semantics.

---

## Semantic Validation

`parse-font-inventory` does not perform semantic validation.

At this stage:

- language normalization is performed
- inference may occur
- warnings may be generated

Semantic validation is deferred to later pipeline stages
(e.g. create-catalog), where strict validation rules may apply.

---

## API reference

::: fontshow.cli.parse_inventory
