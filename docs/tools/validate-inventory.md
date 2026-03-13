# validate-inventory

This module validates a Fontshow inventory file against the project
JSON Schema and runs semantic checks on language metadata.

It operates on an existing inventory file and does not modify it.

---

## Responsibilities

- Load a Fontshow inventory from JSON
- Validate inventory structure against the schema
- Run semantic validation for language codes
- Report validation diagnostics to the CLI

---

## Scope and non-responsibilities

The `validate-inventory` stage is responsible for checking whether an
inventory is structurally and semantically acceptable for downstream use.

It does **not** perform:

- font discovery
- font metadata extraction
- inventory enrichment or normalization
- catalog generation
- LaTeX compilation

In particular:

- the input inventory is treated as read-only
- validation diagnostics are emitted to the CLI only
- no output file is generated

This separation ensures that:

- validation remains explicit and repeatable
- inventory production and inventory checking stay decoupled
- downstream failures can be distinguished from input-data failures

---

## Invocation

Use the top-level dispatcher:

<!-- cheatsheet:start -->
```bash
fontshow validate-inventory <inventory.json>
```
<!-- cheatsheet:end -->

The command validates an existing inventory file and exits after
reporting the result.

---

## Validation behavior

The command performs two layers of checks:

- **Schema validation**
  Confirms that the inventory matches the Fontshow JSON Schema.

- **Semantic validation**
  Reports invalid or suspicious language codes found in inventory
  metadata.

Semantic diagnostics are reported through the CLI and do not produce a
new inventory artifact.

---

## Output

On success, the command prints a confirmation message:

```text
Schema validation passed.
```

On failure, it reports the detected problem, for example:

- missing input file
- invalid JSON
- schema validation failure

Semantic warnings are emitted before the final success message when the
inventory is structurally valid but contains language-code issues.

---

## Exit codes

<!-- cheatsheet:start -->
| Code | Meaning |
| ------ | -------- |
| `0` | Validation completed successfully |
| `1` | Input file missing, invalid JSON, or validation failed |
<!-- cheatsheet:end -->

---

## Notes

- `validate-inventory` is a validation-only command
- it does not enrich or rewrite the inventory
- it is typically run after `parse-inventory` and before `create-catalog`

## API reference

::: fontshow.cli.validate_inventory
