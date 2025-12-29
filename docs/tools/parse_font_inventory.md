# parse_font_inventory

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

Semantic validation is performed by the `fontshow-validate` command and
emits structured warnings without failing the validation process.

---

### Design notes

- Warnings are **informational only** and never block processing.
- Declared metadata is never modified based on warnings.
- The warning system is intentionally minimal and extensible.
- Wrapper functions for warning emission were removed in C4.3 to avoid
  ambiguity and duplicated semantics.


---

## API reference

::: fontshow.parse_font_inventory
