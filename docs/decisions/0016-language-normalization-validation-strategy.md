# Decision 0016 - Language Normalization and Validation Strategy

**Date**: 31/01/2026
**Status**: Accepted

## Context

Font metadata often contains language identifiers that are:

- deprecated
- malformed
- inconsistent in casing or structure
- partially compliant with BCP-47
- derived from heterogeneous upstream sources

Historically, Fontshow handled these inconsistencies implicitly during
inventory parsing, with behavior documented partially in `pipeline.md`
and partially in code.

As the project evolved, this led to:

- unclear responsibility boundaries
- duplicated documentation
- ambiguity between normalization and validation
- difficulty reasoning about strict vs permissive behavior

A formal decision was required to clarify intent and stabilize behavior.

---

## Decision

Fontshow adopts a **two-stage language handling model**:

1. **Normalization**
2. **Validation**

These stages are conceptually distinct and intentionally decoupled.

---

## 1. Normalization

Normalization is a best-effort transformation applied during
inventory parsing.

Its goals are to:

- improve consistency of language tags
- reduce noise from legacy or non-standard metadata
- preserve semantic intent where possible

Normalization MAY include:

- canonical casing
- mapping deprecated subtags
- removal of unsupported private extensions
- normalization of known legacy forms

Normalization:

- does **not** guarantee correctness
- does **not** enforce standards
- does **not** fail the pipeline

It exists solely to improve downstream usability.

---

## 2. Validation

Validation determines whether language tags are acceptable under a
given policy.

Fontshow supports two validation modes:

### 2.1 Permissive mode (default)

- Invalid or deprecated tags are accepted
- Warnings may be emitted
- Processing continues
- Normalized values may be used

This mode prioritizes compatibility with real-world font metadata.

---

### 2.2 Strict mode (`--strict-bcp47`)

- Only RFC-compliant BCP-47 tags are allowed
- Deprecated or malformed tags cause failure
- No silent normalization is performed
- Execution stops on first violation

Strict mode is opt-in and intended for:

- CI environments
- data quality validation
- regression detection

---

## Non-Goals

This decision explicitly does **not** include:

- automatic language inference
- linguistic correctness guarantees
- silent correction of invalid metadata
- changes to inventory schema
- implicit behavior changes

---

## Consequences

### Positive

- Clear separation of concerns
- Deterministic behavior
- Improved documentation consistency
- Safe support for both strict and permissive workflows

### Trade-offs

- Slightly more complexity in documentation
- Users must explicitly enable strict validation
- Some invalid real-world data remains accepted by default

---

## Relation to Semantic Validation

Language normalization and semantic validation are separate concerns.

Normalization:

- transforms input into canonical form
- never fails execution

Semantic validation:

- evaluates correctness of normalized data
- may fail execution when strict mode is enabled
- is applied at catalog generation time

---

## Related Documentation

- `docs/tools/parse-inventory.md`
- `docs/pipeline.md`
- `docs/schema/inventory-1.1.md`

---

## Rationale

This design preserves backward compatibility while enabling:

- stronger validation in controlled environments
- clearer reasoning about failures
- future extensibility without breaking behavior

It reflects the principle that **normalization and validation are distinct
concerns and must not be conflated**.
