# Font Inventory Schema v1.2

## NOTE

The runtime JSON schema is the sole **source of truth** lives in:

src/fontshow/schema/inventory_v1_2.json

This document is a human-oriented explanation of that schema.

## Full JSON Schema

<!-- SCHEMA_JSON_START -->

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:fontshow:schema:inventory:1.2",
  "title": "Fontshow Inventory Schema v1.2",
  "type": "object",
  "required": [
    "metadata",
    "fonts"
  ],
  "additionalProperties": false,
  "properties": {
    "metadata": {
      "type": "object",
      "required": [
        "schema_version",
        "input_inventory_tool",
        "input_inventory_tool_version",
        "inference_level",
        "fonttools",
        "run_environment"
      ],
      "additionalProperties": false,
      "properties": {
        "schema_version": {
          "type": "string",
          "const": "1.2"
        },
        "input_inventory_tool": {
          "type": "string",
          "minLength": 1
        },
        "input_inventory_tool_version": {
          "type": "string",
          "minLength": 1
        },
        "inference_level": {
          "type": "string",
          "minLength": 1
        },
        "fonttools": {
          "type": "object",
          "required": [
            "available",
            "fontconfig_charset_included",
            "version"
          ],
          "additionalProperties": false,
          "properties": {
            "available": {
              "type": "boolean"
            },
            "fontconfig_charset_included": {
              "type": "boolean"
            },
            "version": {
              "type": "string",
              "minLength": 1
            }
          }
        },
        "run_environment": {
          "type": "object",
          "description": "Minimal system identification for reproducibility and diagnostics.",
          "required": [
            "os",
            "os_release",
            "kernel",
            "machine",
            "python_version",
            "hostname",
            "execution_context"
          ],
          "additionalProperties": true,
          "properties": {
            "os": {
              "type": "string",
              "minLength": 1
            },
            "os_release": {
              "type": "string",
              "minLength": 1
            },
            "kernel": {
              "type": "string",
              "minLength": 1
            },
            "machine": {
              "type": "string",
              "minLength": 1
            },
            "python_version": {
              "type": "string",
              "minLength": 1
            },
            "hostname": {
              "type": "string",
              "minLength": 1
            },
            "execution_context": {
              "type": "string",
              "enum": [
                "native",
                "wsl",
                "container",
                "other"
              ]
            }
          }
        }
      }
    },
    "fonts": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/font_entry"
      }
    }
  },
  "$defs": {
    "font_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "path",
        "family",
        "subfamily",
        "typographic_subfamily",
        "full_name",
        "postscript_name",
        "version_string",
        "unique_font_id",
        "units_per_em",
        "ascent",
        "descent",
        "weight_class",
        "width_class",
        "italic_angle",
        "is_fixed_pitch",
        "glyph_count",
        "coverage",
        "inference",
        "charset",
        "sample_text",
        "specimen_text",
        "specimen_strategy",
        "specimen_glyph_count"
      ],
      "properties": {
        "path": {
          "type": "string",
          "minLength": 1,
          "description": "Canonical font file path. Multiple faces in the same file share this path."
        },
        "family": {
          "type": "string",
          "minLength": 1
        },
        "subfamily": {
          "type": "string",
          "minLength": 1
        },
        "typographic_subfamily": {
          "type": [
            "string",
            "null"
          ]
        },
        "full_name": {
          "type": "string",
          "minLength": 1
        },
        "postscript_name": {
          "type": "string",
          "minLength": 1
        },
        "version_string": {
          "type": "string",
          "minLength": 1
        },
        "unique_font_id": {
          "type": "string",
          "minLength": 1
        },
        "units_per_em": {
          "type": "integer",
          "minimum": 1
        },
        "ascent": {
          "type": "integer"
        },
        "descent": {
          "type": "integer"
        },
        "weight_class": {
          "type": "integer",
          "minimum": 1,
          "maximum": 1000
        },
        "width_class": {
          "type": "integer",
          "minimum": 1,
          "maximum": 9
        },
        "italic_angle": {
          "type": "number"
        },
        "is_fixed_pitch": {
          "type": "boolean"
        },
        "glyph_count": {
          "type": "integer",
          "minimum": 1
        },
        "coverage": {
          "type": "object",
          "additionalProperties": true
        },
        "inference": {
          "type": "object",
          "additionalProperties": true
        },
        "charset": {
          "type": "object",
          "additionalProperties": true
        },
        "sample_text": {
          "type": "object",
          "required": [
            "source",
            "text"
          ],
          "additionalProperties": false,
          "properties": {
            "source": {
              "type": "string",
              "const": "font"
            },
            "text": {
              "type": "string"
            }
          }
        },
        "specimen_text": {
          "type": "string",
          "minLength": 1
        },
        "specimen_strategy": {
          "type": "string",
          "enum": [
            "internal",
            "script",
            "cmap",
            "deferred"
          ]
        },
        "specimen_glyph_count": {
          "type": [
            "integer",
            "null"
          ],
          "minimum": 1
        },
        "specimen_rejection_reason": {
          "type": [
            "string",
            "null"
          ]
        },
        "warnings": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/warning"
          }
        }
      }
    },
    "warning": {
      "type": "object",
      "required": [
        "code",
        "message",
        "severity"
      ],
      "additionalProperties": false,
      "properties": {
        "code": {
          "type": "string",
          "minLength": 1
        },
        "message": {
          "type": "string",
          "minLength": 1
        },
        "severity": {
          "type": "string",
          "enum": [
            "info",
            "warning",
            "error"
          ]
        }
      }
    }
  }
}
```

<!-- SCHEMA_JSON_END -->

## Overview

Schema **v1.2** is the single authoritative schema for the Fontshow inventory.
Previous schemas **v1.0** and **v1.1** are deprecated and archived.

This schema guarantees:

* Deterministic inventory structure
* Strict typing
* Canonical font identity
* Robust specimen generation (Issue #54)
* Reproducibility across systems
* Simplified validation and maintenance

---

## Root Structure

```json
{
  "metadata": {...},
  "fonts": [...]
}
```

---

## Metadata

Required fields:

* `schema_version` = `"1.2"`
* `input_inventory_tool`
* `input_inventory_tool_version`
* `inference_level`
* `run_environment`

### run_environment

Identifies the system where Fontshow executed:

* `os`
* `os_release`
* `kernel`
* `machine`
* `python_version`
* `hostname`

---

## Font Entry

Each entry represents **one font face**.

Multiple faces in a single font file (TTC/collections) are represented by **multiple entries sharing the same `path`**.

---

## Canonical Path Rule

* Exactly one `path` per font entry
* No duplicated path in identity
* Multiple faces → same path, different identity

---

## Deterministic Identity (Required)

* `family`
* `subfamily`
* `typographic_subfamily`
* `full_name`
* `postscript_name`
* `version_string`
* `unique_font_id`

Ensures stable, cross-platform identification.

---

## Technical Core Metrics (Required)

* `units_per_em`
* `ascent`
* `descent`
* `weight_class`
* `width_class`
* `italic_angle`
* `is_fixed_pitch`
* `glyph_count`

Used for diagnostics and reproducibility.

---

## Coverage, Inference, Charset

Preserved from previous schemas; structure unchanged.

---

## Embedded Sample Text

```json
sample_text = {
  "source": "font",
  "text": ...
}
```

Raw internal sample from font, not guaranteed valid for rendering.

---

## Deterministic Specimen (Issue #54)

Required fields:

* `specimen_text`
* `specimen_strategy` (`internal | script | cmap | deferred`)
* `specimen_glyph_count`

Optional:

* `specimen_rejection_reason`

### Strategy

1. Internal sample (validated)
2. Script-aware sample
3. Cmap-driven fallback (guaranteed safe)

Ensures LuaLaTeX subset never fails.

---

## Font-Level Warnings (Optional)

```json
warnings = [
  { code, message, severity }
]
```

Severity enum: `info | warning | error`.

---

## Determinism Guarantees

* Same font → identical specimen across runs
* No randomness
* Canonical identity
* Strict schema validation

---

## Migration

* Regenerate inventory using current pipeline
* v1.0 and v1.1 inventories unsupported

---

## Related

* ADR 0020 — Schema v1.2 Unification
* ADR 0019 — Enum JSON representation
* Issue #54 — Robust specimen fallback
