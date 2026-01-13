# Archived after base-zero planning (v0.28.7.post14)

# Session 1 Checklist — Issue 1
Finalize dual-field language strategy (raw vs normalized)

## Goal of the session

Define a **clear, explicit, and stable contract** for language-related fields
before any code or schema changes.

No implementation is allowed in this session.

---

## 1. Inventory schema audit

### Files to inspect

- docs/schema/font_inventory.schema.json
- docs/schema/partials/ (if present)
- docs/data_dictionary.md

### Checklist

- [ ] Identify all fields related to languages
- [ ] Note current definitions, types, and constraints
- [ ] Verify which fields are:
  - required
  - optional
  - nullable
- [ ] Identify validation rules currently enforced by schema
- [ ] Note any ambiguity or overlap between fields

### Output

- Written notes describing current schema semantics
- List of unclear or overloaded fields

---

## 2. Enrichment logic audit

### Files to inspect

- fontshow/parse_font_inventory.py
- fontshow/inference/languages.py (or equivalent)
- fontshow/inference/__init__.py

### Checklist

- [ ] Identify where Fontconfig language tags enter the pipeline
- [ ] Track transformations applied to language data
- [ ] Verify whether raw data is ever modified or filtered
- [ ] Identify where ISO normalization happens
- [ ] Identify where validation is applied (and on which field)

### Output

- Flow description: raw → normalized → validated
- List of implicit assumptions in code

---

## 3. Validation & warning audit

### Files to inspect

- fontshow/validation/validate_language_codes.py
- fontshow/validation/__init__.py
- docs/decisions.md (language-related sections)

### Checklist

- [ ] Identify which fields are subject to ISO 639 validation
- [ ] Identify warning codes emitted for invalid language tags
- [ ] Check whether validation failures affect:
  - raw data
  - normalized data
- [ ] Identify current warning severity and intent

### Output

- Table mapping:
  - field → validation rule → warning/error
- List of mismatches between intent and behavior

---

## 4. Documentation contract audit

### Files to inspect

- docs/decisions.md
- docs/data_dictionary.md
- docs/architecture.md (language-related sections)

### Checklist

- [ ] Verify whether dual-field strategy is explicitly documented
- [ ] Identify contradictions between docs and code
- [ ] Identify undocumented assumptions
- [ ] Check if lossiness is documented as intentional

### Output

- List of documentation gaps
- Notes on wording that implies guarantees not actually provided

---

## 5. Environment evidence check (Gentoo focus)

### Inputs

- Existing Gentoo pipeline runs
- Known problematic language tags (e.g. ku-tr, zh-cn, lzh(s), etc.)

### Checklist

- [ ] Confirm which tags appear in raw inventories
- [ ] Confirm which tags trigger validation warnings
- [ ] Identify which warnings are considered noise vs signal
- [ ] Confirm that raw tags are useful for diagnostics/debugging

### Output

- Short list of representative real-world examples
- Decision notes on what must be preserved verbatim

---

## 6. Contract decisions to be written (no code yet)

### Required decisions

- [ ] Which field is authoritative for validation?
- [ ] Is normalization allowed to be lossy?
- [ ] Can normalized languages be empty while raw is not?
- [ ] Are raw language tags ever subject to schema validation?
- [ ] How does this interact with schema_version guarantees?

### Output

- Bullet-point contract draft
- Ready-to-implement ruleset

---

## 7. End-of-session deliverables

Before closing the session, ensure you have:

- [ ] A written contract draft (notes or markdown)
- [ ] A list of concrete changes required in:
  - schema
  - enrichment logic
  - validation
  - documentation
- [ ] A clear “non-goals” list

---

## Stop condition

❗ Do NOT:
- modify code
- modify schema
- update tests

This session ends when the contract is explicit and unambiguous.
