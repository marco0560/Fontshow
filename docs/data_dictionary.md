# Data Dictionary

This document defines the **normative JSON schema** used by Fontshow.
All inventories generated or processed by Fontshow tools MUST conform
to the structures described here.

The dictionary describes:

- extracted metadata
- pass-through metadata
- inferred / derived metadata

---

## Top-level structure

```json
{
  "metadata": { ... },
  "fonts": [ ... ]
}
```

---

## metadata

Metadata about how and when the inventory was generated or enriched.

### Fields

- `schema_version` (string)
  Inventory schema version.

- `generated_at` (string, ISO 8601)

- `tool` (string)
  Name of the tool that produced the inventory (`dump-fonts`,
  `parse-inventory`, `validate-inventory`, `create-catalog`).

- `tool_version` (string)
  Fontshow version used by the tool.

- `environment` (object)
  - `hostname` (string)
  - `username` (string)
  - `os` (string)
  - `kernel` (string)
  - `platform` (string)
  - `execution_context` (object)
    - `type` (string, e.g. `native`, `wsl`, `container`)

- `fontconfig_charset_included` (boolean)

- `fonttools_available` (boolean)

- `inference_level` (string, optional)
  Inference strategy used when enriching the inventory.

- `input_inventory_tool` (string, optional)
- `input_inventory_tool_version` (string, optional)

---

## fonts

List of font entries.
Each entry represents a **font file**, not an individual face.

---

## Font entry

### identity

Font identity and naming metadata.

- `file` (string)
  Canonical path to the font file.

- `ttc_index` (integer or null)

- `family` (string or null)

- `style` (string or null)

- `fullname` (string or null)

- `postscript_name` (string or null)

- `id` (string)
  Stable internal identifier.

---

### platform

- `name` (string)
  Platform where the font was discovered (e.g. `linux`, `windows`).

---

### format

Font container and format classification.

- `container` (string, e.g. `TTF`, `OTF`, `TTC`)
- `font_type` (string)
- `ttc_index` (integer or null)
- `ttc_count` (integer or null)
- `variable` (boolean)
- `color` (boolean)
- `decorative` (boolean)

---

### coverage

Raw and derived coverage metadata.
Coverage fields are descriptive and diagnostic; no inference or semantic
decisions are performed at this level.

- `unicode`
  - `count` (integer)
  - `min` (integer)
  - `max` (integer)

- `unicode_blocks` (object)
  Mapping of Unicode block names to approximate coverage metrics.
  This data is typically extracted from external tools or inventory sources.

- `scripts` (list of strings)
  Script tags declared by FontConfig (ISO 15924 / OpenType).

- `languages` (list of strings)
  Language tags declared by FontConfig (`lang:`), BCP-47 style.

- `charset` (object or null)
  Raw FontConfig charset ranges, when enabled at extraction time.
  This data is file-level, best-effort, and not normalized.

---

#### Charset-derived coverage (diagnostic)

The following fields are derived from FontConfig charset data when available.
They are **diagnostic only** and do not affect inference logic.

- `normalized_charset` (object)
  Deterministic normalization of raw charset ranges.
  Ranges are sorted and merged, and a total codepoint count is computed.

  - `ranges` (list of `[start, end]` integer pairs)
  - `codepoints_count` (integer)

- `unicode_blocks_from_charset` (object)
  Mapping of Unicode block names to the number of codepoints covered by the
  normalized charset.
  This field does not replace `coverage.unicode_blocks`.

- `script_coverage_from_charset` (object)
  Mapping of script tags (ISO 15924) to estimated coverage ratios
  (floating-point values between 0.0 and 1.0).
  This data is informational and non-authoritative.

---

### typography

Typography-related metadata.

- `weight_class` (integer)
- `width_class` (integer)
- `opentype_features` (list of strings)

---

### classification

High-level font classification flags.

- `is_variable` (boolean)
- `is_color` (boolean)
- `is_decorative` (boolean)
- `is_emoji` (boolean)
- `container` (string)
- `font_type` (string)

---

### license

Font license information.

- `text` (string or null)
- `url` (string or null)

---

### vendor

- `vendor` (string or null)

---

### embedding_rights

- `embedding_rights` (integer)

---

### sample_text

- `sample_text` (string or null)
  Optional sample text extracted from the font.

---

### source

Extraction diagnostics.

- `fonttools`
  - `ok` (boolean)
  - `error` (string or null)

- `fontconfig`
  - `ok` (boolean)

---

## inference

Derived metadata computed by `parse-inventory`.

Inference is deterministic and reproducible.

- `level` (string)

- `scripts` (list of strings)
  Inferred ISO 15924 scripts.

- `languages` (list of strings)
  Languages inferred from scripts.

- `declared_scripts` (list of strings)
  Raw scripts copied from `coverage.scripts`.

- `declared_languages` (list of strings)
  Raw languages copied from `coverage.languages`.

- `unicode_blocks` (object)
  Unicode blocks reused for inference diagnostics.

---

### `fonts[].inference.scripts`

**Type:** `array[string]`
**Required:** no
**Values:** ISO 15924 script codes (lowercase)
**Example:** `["latn"]`, `["cyrl", "grek"]`, `["jpan"]`

This field contains the list of writing systems inferred for a font, expressed
using **ISO 15924** script codes.

#### Derivation rules

The value is derived by `parse-inventory` using a best-effort strategy
based on Unicode coverage metadata:

1. **Primary source**: `coverage.unicode_blocks`
   If available, Unicode block usage statistics are analyzed to infer scripts.
   Only blocks with significant coverage are considered.

2. **Fallback source**: `coverage.unicode.max`
   If block-level data is unavailable, the maximum Unicode code point supported
   by the font is used as a heuristic indicator.

3. **Normalization**
   All inferred scripts are normalized to ISO 15924 codes:
   - `Latin` → `latn`
   - `Greek` → `grek`
   - `Cyrillic` → `cyrl`
   - `Arabic` → `arab`
   - `Hebrew` → `hebr`
   - `Devanagari` → `deva`
   - CJK disambiguation:
     - Han only → `hani`
     - Han + Japanese kana → `jpan`
     - Han + Hangul → `hang`

4. **Unknown**
   If no reliable inference is possible, the value defaults to:

   ```json
   ["unknown"]
   ```

#### Notes

- This field represents **inferred** information and may differ from
  language declarations.
- The absence of this field does not invalidate a font entry.
- Downstream tools must treat `"unknown"` as a valid placeholder.

---

## Overall Notes

- `coverage.*` fields are never modified by inference.
- `inference.*` fields may evolve as inference logic improves.
- Consumers SHOULD rely on `inference` rather than `coverage`
  unless raw metadata is explicitly required.
