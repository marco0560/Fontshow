# Archived after base-zero planning (v0.28.7.post14)

# Milestone 0.29.0 — C5.X Stabilization
Task-by-task Execution Plan

## Milestone Goal

Stabilize the C5.X refinement phase by:
- reducing validation noise,
- making semantic contracts explicit,
- aligning logging documentation and implementation,
- improving observability and readability,

**without introducing new semantic features**.

---

## Issue 1 — Finalize dual-field language strategy
(raw Fontconfig tags vs normalized ISO 639)

### Session 1 — Analysis & Contract Definition

- Review current usage of:
  - `coverage.languages`
  - `coverage.languages_raw`
- Identify ambiguities in:
  - validation rules
  - nullability
  - schema constraints
- Decide and document:
  - authoritative source for validation
  - allowed lossiness
  - interaction with schema_version

**Checkpoint**
- Clear written contract (notes or draft decision)

---

### Session 2 — Implementation

- Update enrichment logic in `parse_font_inventory`
- Ensure raw language tags are preserved verbatim
- Normalize ISO 639 codes in a dedicated field
- Update semantic validation rules
- Update JSON Schema accordingly
- Fix or extend existing tests

**Checkpoint**
- Schema validation passes
- No unexpected new warnings

---

### Session 3 — Documentation & Verification

- Update `decisions.md`
- Update `data_dictionary.md`
- Run full pipeline on Gentoo
- Confirm validation noise is reduced

**Done criteria**
- Gentoo pipeline runs clean
- Raw vs normalized semantics are explicit and documented

---

## Issue 2 — Charset vs fontTools coverage consistency diagnostics
(logging-only)

### Single session

- Identify point where both data sources are available
- Implement at least one diagnostic:
  - charset coverage significantly smaller/larger
  - non-overlapping Unicode blocks
- Emit diagnostics via structured logging only
- Ensure:
  - no inventory mutation
  - suppressible via log level
- Add focused tests:
  - both sources present
  - one source missing
- Update documentation explaining diagnostic-only intent

**Done criteria**
- Diagnostics observable
- Zero semantic changes

---

## Issue 3 — Close logging specification vs implementation gap

### Session 1 — Audit

- Extract logging matrices from `decisions.md`
- Classify each message as:
  - implemented
  - missing
  - intentionally deferred
- Annotate gaps explicitly

---

### Session 2 — Alignment

- Implement a small, low-risk subset of missing messages
- Explicitly mark deferred messages in documentation
- Ensure no undocumented discrepancies remain

**Done criteria**
- Logging spec is an explicit contract
- No ambiguity between docs and code

---

## Issue 4 — Improve JSON readability for charset-derived arrays

### Single session

- Identify JSON serializer / formatter
- Implement compact formatting for short numeric arrays
- Ensure change is localized to formatting layer
- Add snapshot test for JSON output
- Verify schema and semantics are unchanged

**Done criteria**
- Improved readability
- No behavioral changes

---

## Recommended commit sequence

1. `feat(schema): finalize dual-field language strategy`
2. `chore(logging): add charset vs fontTools diagnostics`
3. `docs(logging): align logging spec with implementation`
4. `chore(format): improve JSON readability for numeric ranges`

---

## Milestone Completion Criteria

- No increase in validation noise
- Gentoo pipeline runs clean
- No breaking changes
- All issues independently closable
