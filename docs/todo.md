# Fontshow – TODO & Technical Debt List

This document tracks pending tasks, technical debt, and planned validations for the Fontshow project.
It is intended as a **living document**, to be refined as features stabilize and automated testing is introduced.

---

## 1️⃣ Native Linux (Gentoo) Testing 🧪 **HIGH PRIORITY**

### 1.1 Fontconfig charset extraction (`--include-fc-charset`)
**Status:** ⏳ Pending
**Rationale:** On Fedora / WSL, `fc-query` cannot reliably extract charset information.
Gentoo may behave differently depending on Fontconfig build options.

**Tests to perform:**
- [ ] Does `fc-query file.ttf` work on Gentoo?
- [ ] Does `fc-query "family:style=Regular"` work?
- [ ] Does `dump_fonts --include-fc-charset` produce non-null `charset` entries?
- [ ] Compare behavior across:
  - TrueType fonts
  - OpenType fonts
  - Type1 fonts (`.t1`)
  - Variable fonts (`[wght]`)

**Expected outcome:**
- At least some fonts expose `charset` data
- Confirmation or rejection of this feature’s usefulness on Gentoo

---

### 1.2 `dump_fonts` robustness
**Status:** 🧪 Pending

**Scenarios:**
- [ ] System with many fonts (>500)
- [ ] System with very few fonts
- [ ] Fonts with non-standard paths
- [ ] Fonts with unusual / Unicode names
- [ ] Duplicate family/style combinations

---

## 2️⃣ `parse_font_inventory` – Validation & Resilience ⚙️

### 2.1 Soft validation coverage
**Status:** ✔️ Partially implemented

**Remaining improvements:**
- [ ] Warn on inconsistent `coverage`
- [ ] Warn on missing or empty `style`
- [ ] Warn on invalid or non-numeric `weight`
- [ ] Warn on missing or unreadable font `path`

⚠️ All issues must remain **warnings**, never fatal errors.

---

### 2.2 `--validate-inventory` as a diagnostic tool
**Status:** ⏳ Pending

**Possible extensions:**
- [ ] Final summary with warning counts by category
- [ ] `--validate-inventory --strict` (non-zero exit on warnings)
- [ ] Optional JSON output (future CI integration)

---

## 3️⃣ `create_catalog` & LaTeX Quality 📄 **MEDIUM PRIORITY**

### 3.1 LaTeX debugging facilities
**Status:** ⏳ Pending

**Planned options:**
- [ ] `--dump-tex-per-font`
- [ ] `--keep-temp`
- [ ] `--debug-font <FONT_NAME>`
- [ ] Per-font LaTeX banner with diagnostic metadata

---

### 3.2 LuaLaTeX robustness tests
**Scenarios:**
- [ ] Symbol-only fonts
- [ ] Fonts without ASCII glyphs
- [ ] Fonts with uncommon encodings
- [ ] Fonts known to crash LuaTeX

---

## 4️⃣ JSON Schema & Versioning 📦

### 4.1 Inventory schema evolution
**Status:** ⏳ Pending

**Tasks:**
- [ ] Formalize `schema_version`
- [ ] Define backward compatibility rules (1.x)
- [ ] Clearly mark required vs optional fields
- [ ] Provide example JSON files per schema version

---

### 4.2 Tool versioning alignment
**Status:** ⚠️ Partial

**To be clarified:**
- [ ] Relationship between `tool_version` and `fontshow.__version__`
- [ ] Consistent version reporting in:
  - `dump_fonts`
  - `parse_font_inventory`
  - `create_catalog`
- [ ] Documentation of versioning policy

---

## 5️⃣ Manual Testing Documentation 🧪

### 5.1 `docs/testing.md`
**Status:** 🟡 In progress

**To be added:**
- [ ] Gentoo test results
- [ ] Fedora test results
- [ ] WSL test results
- [ ] Native Windows test results (if feasible)
- [ ] Documented edge cases and known failures

This document will serve as the basis for future automated tests.

---

## 6️⃣ Packaging & CLI UX 🧰

### 6.1 CLI entry points
**Status:** ⏳ Pending

**Evaluate replacing:**
\```bash
python -m fontshow.dump_fonts
\```

with:
\```bash
fontshow dump
fontshow parse
fontshow catalog
\```

---

### 6.2 CLI consistency
- [ ] Standardize `--dry-run` where applicable
- [ ] Introduce `--verbose` / `--quiet`
- [ ] Ensure consistent exit codes across tools

---

## 7️⃣ Repository Hygiene 🧹

### 7.1 `clean_repo.py`
**Status:** ✔️ Implemented

**Possible enhancements:**
- [ ] `--all` vs safe default mode
- [ ] Optional JSON output
- [ ] Optional integration with pre-push hooks

---

## 8️⃣ CI & Automation (Future) 🚀

**Status:** 💤 Parked

**Ideas for later stages:**
- [ ] CI: lint + type checking only
- [ ] CI without real fonts (mocked inventory)
- [ ] Non-regression tests on JSON schema evolution

---

*Last updated: see git history.*
