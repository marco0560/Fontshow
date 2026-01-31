# Language normalization

## Language normalization semantics

This document defines how Fontshow processes language identifiers extracted
from font metadata.

Language handling is intentionally separated into two concerns:

- normalization
- validation

These concepts are related but not equivalent.

---

## Normalization

Normalization is a best-effort transformation applied to language tags in
order to improve consistency and downstream usability.

Normalization MAY include:

- canonical casing
- replacement of deprecated subtags
- removal of unsupported private-use extensions
- mapping of legacy identifiers to modern equivalents

Normalization:

- does not guarantee correctness
- does not enforce standards
- does not fail the pipeline

Its purpose is to reduce noise, not to validate input.

---

## Validation

Validation determines whether a language tag is acceptable under a given
policy.

Two validation modes exist:

### Permissive (default)

- Invalid or deprecated tags are accepted
- Warnings may be emitted
- Processing continues

### Strict (`--strict-bcp47`)

- Only RFC-compliant BCP-47 tags are allowed
- Deprecated or malformed tags cause failure
- No silent normalization is performed

---

## Design constraints

- Normalization must never imply correctness
- Validation must never silently modify data
- Enforcement must always be explicit
- Behavior must be observable and documented

---

## Non-goals

- Automatic language inference
- Linguistic correctness guarantees
- Silent mutation of source metadata
