# Decision 0022 - Fontshow — Specimen Inference Inputs Matrix v1.0

**Date**: 02/03/2026
**Status**: Accepted
**Type**: AUTHORITATIVE DESIGN CONTRACT
**Applies to**: schema ≥ v1.2
**Phases**: dump-fonts → parse-inventory

---

## 1. Architectural Principle

Fontshow follows a strict two-phase pipeline:

```text
    Discovery Phase  (dump-fonts)
        ↓ produces IR (font_inventory.json)
    Interpretation Phase (parse-inventory)
        ↓ produces enriched IR
```

### Hard Rule

parse-inventory MUST operate as:

```text
    JSON → JSON (pure transformation)
```

and MUST NOT access font files.

All font-dependent data must be collected during dump-fonts.

---

## 2. Terminology

| Term      | Meaning                                       |
|-----------|-----------------------------------------------|
| Signal    | Raw observable fact extracted from font       |
| Inference | Semantic interpretation derived from signals  |
| Specimen  | Representative text shown for catalog display |

---

## 3. Specimen Generation Responsibilities

### dump-fonts (Discovery)

MUST collect signals only.

Allowed:

- Read font files
- Extract raw metadata
- Export coverage information

Forbidden:

- Language inference
- Script inference
- Specimen selection
- Heuristic interpretation

---

### parse-inventory (Interpretation)

MUST:

- derive specimen deterministically
- rely exclusively on inventory JSON
- never open font files

---

## 4. Required Signals (Dump Output)

These fields MUST exist or be derivable from dump output.

### 4.1 Unicode Coverage (existing)

```json
"unicode_blocks": {...}
```

Purpose:

- script inference
- language inference

---

### 4.2 Charset Ranges (NEW — REQUIRED)

Compact synthesis of cmap coverage.

```json
"charset_ranges": [
  [32,126],
  [160,255]
]
```

Definition:

```text
    charset_ranges := merged contiguous Unicode codepoint ranges
                      present in cmap tables.
```

Properties:

- lossless for coverage queries
- deterministic
- small storage footprint
- replaces cmap reopening

---

### 4.3 Glyph Count (NEW — REQUIRED)

```json
"glyph_count": 1342
```

Definition:
Total glyphs in font.

Used for:

- specimen sizing heuristics
- density estimation
- catalog diagnostics

No semantic interpretation implied.

---

### 4.4 Sample Text (existing)

```json
"sample_text": ["Example text"]
```

Meaning:
Embedded font-provided specimen.

Highest authority signal.

---

## 5. Specimen Inference Decision Tree

Performed ONLY in parse-inventory.
Specimen inference is deferred from dump-fonts to parse-inventory.
Schema extended with "deferred" specimen_strategy state.

### Step 1 — Internal specimen

IF `sample_text` exists:

```text
specimen_text       := sample_text
specimen_strategy   := "internal"
specimen_glyph_count := glyph_count(sample_text)
STOP
```

---

### Step 2 — Script-aware synthesis

Inputs:

- charset_ranges
- inferred scripts
- unicode_blocks

Algorithm:

```text
alphabet := canonical script alphabet
available := alphabet ∩ charset_ranges
specimen := deterministic subset(available)
```

Output:

```text
specimen_strategy := "script"
```

---

### Step 3 — Coverage fallback

If script synthesis insufficient:

```text
specimen := representative characters
            selected from available coverage
```

Output:

```text
specimen_strategy := "coverage"
```

---

### Step 4 — Minimal fallback

If only sparse coverage exists:

```text
specimen := smallest valid printable subset
```

Output:

```text
specimen_strategy := "minimal"
```

---

## 6. Explicit Non-Goals

Specimen generation MUST NOT:

- reject numeric-only fonts
- assume alphabetic usage
- enforce typographic expectations
- modify discovery data

Catalog is descriptive, not prescriptive.

---

## 7. Determinism Requirements

Given identical input inventory:

- specimen_text MUST be identical
- ordering MUST be stable
- no randomness allowed
- no environment dependence

---

## 8. Performance Guarantees

After compliance:

parse-inventory complexity:

```text
    O(number_of_fonts)
```

with NO font IO.

Expected runtime reduction:

```text
    ~20–60s → ~2–4s on large systems.
```

---

## 9. Regression Guard

Any future change introducing:

```text
    TTFont(...)
    fontTools access
    filesystem reads
```

inside parse-inventory is a CONTRACT VIOLATION.

---

END OF CONTRACT
