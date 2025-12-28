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
  Name of the tool that produced the inventory (`dump_fonts`,
  `parse_font_inventory`, `create_catalog`).

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

Raw, declarative coverage metadata.
No inference or normalization is performed here.

- `unicode`
  - `count` (integer)
  - `min` (integer)
  - `max` (integer)

- `unicode_blocks` (object)
  Mapping of Unicode block names to approximate coverage metrics.

- `scripts` (list of strings)
  Script tags declared by FontConfig (ISO 15924 / OpenType).

- `languages` (list of strings)
  Language tags declared by FontConfig (`lang:`), BCP-47 style.

- `charset` (object or null)
  Raw FontConfig charset ranges.

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

Derived metadata computed by `parse_font_inventory`.

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

## Notes

- `coverage.*` fields are never modified by inference.
- `inference.*` fields may evolve as inference logic improves.
- Consumers SHOULD rely on `inference` rather than `coverage`
  unless raw metadata is explicitly required.
