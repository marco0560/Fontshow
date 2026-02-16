# Decision 0019 - Enum / JSON Boundary Invariant

**Date**: 16/02/2026
**Status**: Accepted
**Scope**: Core serialization / typing / inventory pipeline

---

## Context

Fontshow uses structured JSON inventories as a persistent interchange format between
pipeline stages (`dump_fonts → parse_inventory → create_catalog → …`).

Internally, the system relies on **strong typing and Enum semantics** (notably
`Severity` and future similar types). However, JSON has no native Enum type and
represents values as strings.

Historically, mixed representations (`Enum | str`) caused:

- silent drift between in-memory and serialized state
- inconsistent behavior across modules
- fragile typing and hidden conversions
- schema instability
- hard-to-trace bugs

To eliminate these issues, a **strict serialization boundary invariant** was introduced.

---

## Decision

Fontshow enforces a **hard JSON boundary invariant for Enums**:

### In memory

Enums MUST always remain **Enum objects**.

### On disk (JSON)

Enums MUST always be written as **normalized strings**.

### Conversion points (exactly once)

- **JSON → Enum**
  Performed immediately after load via `json_boundary`.

- **Enum → JSON**
  Performed immediately before write via `json_format`.

No other conversions are allowed anywhere in the codebase.

---

## Architectural Invariant

```text
IN-MEMORY:  Enum only
ON-DISK:    normalized string only
CONVERSION: exactly once at JSON boundary
```

Any violation of this invariant is considered an architectural defect.

---

## Rules for introducing new Enums

Whenever a new Enum is added that may cross the JSON boundary:

1. The Enum MUST provide a stable JSON representation
   (e.g. `.to_json()` or equivalent canonical string form).

2. The Enum MUST be registered in `json_boundary` so that:
   - string → Enum conversion occurs immediately after JSON load.

3. `json_format` MUST correctly serialize the Enum to its normalized string.

4. The internal pipeline MUST NOT use `Enum | str` unions.

5. No fallback / implicit conversions may be added outside the JSON boundary.

---

## Non-goals

- No backward compatibility with legacy mixed Enum/string inventories.
- No implicit normalization outside `json_boundary`.
- No support for dual in-memory representations.

Legacy inventories are considered disposable and must be regenerated.

---

## Consequences

### Positive

- Deterministic JSON representation
- Strong typing across the pipeline
- No hidden conversion paths
- Simplified reasoning and debugging
- Schema stability
- Safer refactoring

### Trade-offs

- New Enums require explicit boundary registration
- Slightly stricter development discipline
- External tools must treat Enum values as strings (documented)

---

## Enforcement points

- `json_boundary` → JSON load normalization
- `json_format` → JSON write normalization
- `mypy` → prohibits `Enum | str`
- `ruff` → prevents silent exception / fallback bridges
- CI → ensures invariant is preserved

---

## Developer checklist

When adding a new Enum:

- [ ] Enum class created in `types.py`
- [ ] Stable JSON string representation defined
- [ ] Registered in `json_boundary`
- [ ] Serialized correctly by `json_format`
- [ ] No `Enum | str` introduced
- [ ] Ruff clean
- [ ] Mypy clean
- [ ] Tests green

---

## Related

- `json_boundary.py`
- `json_format.py`
- `Severity` Enum
- Phase T4 — Serialization & typing stabilization

---
