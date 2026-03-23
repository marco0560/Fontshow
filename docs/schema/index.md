# Schema Documentation

## Current Schema

Runtime schema source of truth:

```bash
src/fontshow/schema/inventory_v1_2.json
```

This is the **only supported schema** for Fontshow.

---

## Deprecated Schemas

The following schemas are archived and no longer supported:

* Inventory Schema v1.0
* Inventory Schema v1.1

See: `docs/_archive/schema/`

---

## Documentation

* Font Inventory Schema → `inventory_v1_2.md`
* Language Normalization → `language-normalization.md`

---

## Design Principles

* Single authoritative schema
* Deterministic inventories
* Strict typing
* Canonical font identity
* Reproducibility
* No legacy compatibility

---

## Related Decisions

* ADR 0020 — Schema v1.2 Unification
* ADR 0019 — Enum JSON representation
