# Font Inventory Schema v1.5

## NOTE

The runtime JSON schema is the sole **source of truth** and lives in:

`src/fontshow/schema/inventory_v1_5.json`

This document is a human-oriented rendering of that schema.

<!-- FIELD_REFERENCE_START -->

## Field Reference

| Field | Type | Required | Description |
| ------ | ------ | ---------- | ------------- |
| `$` | object | no | Canonical Fontshow inventory schema for normalized font discovery, enrichment, and LaTeX-oriented validation metadata. |
| `metadata` | object | yes | Inventory-wide metadata describing the producer, runtime environment, and validation context associated with the inventory file. |
| `metadata.schema_version` | string | yes | Schema version identifier for this inventory document. |
| `metadata.input_inventory_tool` | string | yes | Command or component that produced the current inventory payload. |
| `metadata.input_inventory_tool_version` | string | yes | Version string of the tool that produced the current inventory payload. |
| `metadata.inference_level` | string | yes | Inference strictness or enrichment level applied to the inventory. |
| `metadata.fonttools` | object | yes | Versioned metadata about the fontTools extraction surface available when the inventory was produced. |
| `metadata.fonttools.available` | boolean | yes | Whether fontTools was available to the producing command. |
| `metadata.fonttools.fontconfig_charset_included` | boolean | yes | Whether Fontconfig charset-derived information was included in the inventory. |
| `metadata.fonttools.version` | string | yes | fontTools version reported during inventory generation. |
| `metadata.run_environment` | object | yes | Minimal system identification for reproducibility and diagnostics. |
| `metadata.run_environment.os` | string | yes | Operating-system name reported by the producing environment. |
| `metadata.run_environment.os_release` | string | yes | Operating-system release identifier of the producing environment. |
| `metadata.run_environment.kernel` | string | yes | Kernel identifier of the producing environment. |
| `metadata.run_environment.machine` | string | yes | Machine architecture reported by the producing environment. |
| `metadata.run_environment.python_version` | string | yes | Python runtime version used by the producing command. |
| `metadata.run_environment.hostname` | string | yes | Hostname reported by the producing environment. |
| `metadata.run_environment.execution_context` | string | yes | Normalized execution context classification for the producing environment. |
| `metadata.validation` | object | yes | Inventory-wide validation metadata for external runtime surfaces relevant to downstream processing. |
| `metadata.validation.lualatex` | object | yes | Inventory-level LaTeX runtime metadata describing the LuaLaTeX environment associated with validation and loadability decisions. |
| `metadata.validation.lualatex.attempted` | boolean | yes | Whether inventory-wide LuaLaTeX validation or probing has been attempted. |
| `metadata.validation.lualatex.engine` | string \| null | yes | Name of the LaTeX engine associated with the validation metadata. |
| `metadata.validation.lualatex.engine_version` | string \| null | yes | Version string reported by the LaTeX engine. |
| `metadata.validation.lualatex.texlive_version` | string \| null | no | TeX Live release identifier reported by the associated LaTeX runtime, when available. |
| `metadata.validation.lualatex.luaotfload_version` | string \| null | yes | Version of the luaotfload package available in the associated LaTeX runtime. |
| `metadata.validation.lualatex.fontspec_version` | string \| null | yes | Version of the fontspec package available in the associated LaTeX runtime. |
| `metadata.validation.lualatex.polyglossia_version` | string \| null | yes | Version of the Polyglossia package available in the associated LaTeX runtime. |
| `metadata.validation.lualatex.runtime_fingerprint` | string \| null | yes | Stable fingerprint of the relevant LaTeX runtime surface. |
| `metadata.validation.lualatex.render_policy_version` | string \| null | yes | Version or fingerprint of the render-policy inputs associated with validation. |
| `fonts` | array[object] | yes | List of normalized per-face font entries contained in the inventory. |
| `fonts[]` | object | no | Canonical per-face inventory entry containing identity, metrics, enrichment, typography, and validation state. |
| `fonts[].path` | string | yes | Canonical font file path. Multiple faces in the same file share this path. |
| `fonts[].family` | string | yes | Canonical family name associated with the font face. |
| `fonts[].subfamily` | string | yes | Style or face name reported for the font entry. |
| `fonts[].typographic_subfamily` | string \| null | yes | Typographic subfamily name when available, otherwise null. |
| `fonts[].full_name` | string | yes | Human-readable full font face name. |
| `fonts[].postscript_name` | string | yes | PostScript face name used for stable font identification. |
| `fonts[].version_string` | string | yes | Version string extracted from the font metadata. |
| `fonts[].unique_font_id` | string | yes | Deterministic Fontshow identifier for the font face. |
| `fonts[].metrics` | object | yes | Normalized technical metrics and numeric font properties. |
| `fonts[].metrics.units_per_em` | integer | yes | Units-per-em value reported by the font. |
| `fonts[].metrics.ascent` | integer | yes | Ascent metric reported by the font. |
| `fonts[].metrics.descent` | integer | yes | Descent metric reported by the font. |
| `fonts[].metrics.weight_class` | integer | yes | Normalized OS/2 weight class value. |
| `fonts[].metrics.width_class` | integer | yes | Normalized OS/2 width class value. |
| `fonts[].metrics.italic_angle` | number | yes | Italic angle reported by the font. |
| `fonts[].metrics.is_fixed_pitch` | boolean | yes | Whether the font is reported as fixed-pitch or monospaced. |
| `fonts[].metrics.glyph_count` | integer | yes | Number of glyphs reported by the font. |
| `fonts[].coverage` | object | yes | Coverage and Unicode-derived enrichment data associated with the font. |
| `fonts[].inference` | object | yes | Inference outputs derived from coverage, charset, and language processing. |
| `fonts[].charset` | object | yes | Charset-oriented raw or normalized data retained for downstream analysis. |
| `fonts[].typography` | object | yes | Typography-oriented rendering metadata, specimens, and render-policy fields. |
| `fonts[].typography.sample_text` | object | yes | Embedded sample text extracted from the font itself. |
| `fonts[].typography.sample_text.source` | string | yes | Provenance label for the embedded sample text. |
| `fonts[].typography.sample_text.text` | string | yes | Sample text extracted from the font, which may be empty when no embedded sample is available. |
| `fonts[].typography.specimen_text` | string | yes | Final deterministic specimen text chosen for rendering and validation. |
| `fonts[].typography.specimen_strategy` | string | yes | Strategy that produced the final specimen text. |
| `fonts[].typography.specimen_glyph_count` | integer \| null | yes | Count of accepted base glyphs in the final specimen text. |
| `fonts[].typography.specimen_rejection_reason` | string \| null | no | Structured rejection or fallback reason recorded during specimen generation. |
| `fonts[].typography.primary_script` | string \| null | yes | Primary script code selected for the font, when one is available. |
| `fonts[].typography.script_display_name` | string \| null | yes | Human-readable display label associated with the primary script. |
| `fonts[].typography.render_policy` | object | yes | LaTeX-oriented render-policy values derived from the selected script. |
| `fonts[].typography.render_policy.polyglossia_language` | string \| null | yes | Polyglossia language identifier associated with the selected script, when applicable. |
| `fonts[].typography.render_policy.fontspec_opts` | string \| null | yes | fontspec option fragment associated with the selected script, when applicable. |
| `fonts[].typography.script_source` | string \| null | yes | Source from which the primary script decision was derived. |
| `fonts[].typography.opentype_features` | array[string] | no | Reported OpenType feature tags preserved for typography-oriented inspection. |
| `fonts[].typography.opentype_features[]` | string | no | No description. |
| `fonts[].loadability` | object | yes | Per-font persisted loadability state for external rendering engines. |
| `fonts[].loadability.lualatex` | object | yes | Persisted LuaLaTeX loadability result for the current font entry. |
| `fonts[].loadability.lualatex.attempted` | boolean | yes | Whether LuaLaTeX loadability probing has been attempted for this font. |
| `fonts[].loadability.lualatex.loadable` | boolean \| null | yes | Persisted LuaLaTeX loadability result when probing has produced a definitive outcome. |
| `fonts[].loadability.lualatex.reason` | string \| null | yes | Deterministic short reason or failure summary associated with the persisted loadability state. |
| `fonts[].loadability.lualatex.runtime_fingerprint` | string \| null | yes | Runtime fingerprint under which the per-font loadability result was computed. |
| `fonts[].loadability.lualatex.probe_input` | string \| null | yes | Serialized probe input or probe-selection hint associated with the persisted validation attempt. |
| `fonts[].loadability.lualatex.render_variants` | array[object] | yes | Per-render-path LuaLaTeX validation results derived after parse-time script and render-policy enrichment. |
| `fonts[].loadability.lualatex.render_variants[]` | object | no | No description. |
| `fonts[].loadability.lualatex.render_variants[].script` | string | yes | ISO-15924 script code for the validated render path. |
| `fonts[].loadability.lualatex.render_variants[].fontspec_opts` | string \| null | yes | Resolved fontspec option string used for the validated render path. |
| `fonts[].loadability.lualatex.render_variants[].attempted` | boolean | yes | Whether LuaLaTeX validation was attempted for this render path. |
| `fonts[].loadability.lualatex.render_variants[].loadable` | boolean \| null | yes | Persisted LuaLaTeX result for this render path. |
| `fonts[].loadability.lualatex.render_variants[].reason` | string \| null | yes | Deterministic short reason or failure summary for this render path. |
| `fonts[].loadability.lualatex.render_variants[].runtime_fingerprint` | string \| null | yes | Runtime fingerprint under which this render-path result was computed. |
| `fonts[].loadability.lualatex.render_variants[].probe_input` | string \| null | yes | Serialized probe input or probe-selection hint associated with this render-path validation attempt. |
| `fonts[].loadability.lualatex.render_variants[].specimen_text` | string \| null | yes | Validated specimen text that succeeded or was attempted for this render path. |
| `fonts[].loadability.lualatex.render_variants[].specimen_glyph_count` | integer \| null | yes | Accepted base-glyph count for the persisted render-variant specimen. |
| `fonts[].loadability.lualatex.render_variants[].specimen_strategy` | string \| null | yes | Deterministic strategy label describing how the persisted render-variant specimen was produced. |
| `fonts[].warnings` | array[object] | no | Structured warnings attached to the font entry during inventory generation or enrichment. |
| `fonts[].warnings[]` | object | no | Structured warning record attached to an inventory font entry. |
| `fonts[].warnings[].code` | string | yes | Machine-readable warning code. |
| `fonts[].warnings[].message` | string | yes | Human-readable warning message. |
| `fonts[].warnings[].severity` | string | yes | Normalized warning severity. |

<!-- FIELD_REFERENCE_END -->

## Full JSON Schema

<!-- SCHEMA_JSON_START -->

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:fontshow:schema:inventory:1.5",
  "title": "Fontshow Inventory Schema v1.5",
  "description": "Canonical Fontshow inventory schema for normalized font discovery, enrichment, and LaTeX-oriented validation metadata.",
  "type": "object",
  "required": [
    "metadata",
    "fonts"
  ],
  "additionalProperties": false,
  "properties": {
    "metadata": {
      "type": "object",
      "description": "Inventory-wide metadata describing the producer, runtime environment, and validation context associated with the inventory file.",
      "required": [
        "schema_version",
        "input_inventory_tool",
        "input_inventory_tool_version",
        "inference_level",
        "fonttools",
        "run_environment",
        "validation"
      ],
      "additionalProperties": false,
      "properties": {
        "schema_version": {
          "type": "string",
          "const": "1.5",
          "description": "Schema version identifier for this inventory document."
        },
        "input_inventory_tool": {
          "type": "string",
          "minLength": 1,
          "description": "Command or component that produced the current inventory payload."
        },
        "input_inventory_tool_version": {
          "type": "string",
          "minLength": 1,
          "description": "Version string of the tool that produced the current inventory payload."
        },
        "inference_level": {
          "type": "string",
          "minLength": 1,
          "description": "Inference strictness or enrichment level applied to the inventory."
        },
        "fonttools": {
          "type": "object",
          "description": "Versioned metadata about the fontTools extraction surface available when the inventory was produced.",
          "required": [
            "available",
            "fontconfig_charset_included",
            "version"
          ],
          "additionalProperties": false,
          "properties": {
            "available": {
              "type": "boolean",
              "description": "Whether fontTools was available to the producing command."
            },
            "fontconfig_charset_included": {
              "type": "boolean",
              "description": "Whether Fontconfig charset-derived information was included in the inventory."
            },
            "version": {
              "type": "string",
              "minLength": 1,
              "description": "fontTools version reported during inventory generation."
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
              "minLength": 1,
              "description": "Operating-system name reported by the producing environment."
            },
            "os_release": {
              "type": "string",
              "minLength": 1,
              "description": "Operating-system release identifier of the producing environment."
            },
            "kernel": {
              "type": "string",
              "minLength": 1,
              "description": "Kernel identifier of the producing environment."
            },
            "machine": {
              "type": "string",
              "minLength": 1,
              "description": "Machine architecture reported by the producing environment."
            },
            "python_version": {
              "type": "string",
              "minLength": 1,
              "description": "Python runtime version used by the producing command."
            },
            "hostname": {
              "type": "string",
              "minLength": 1,
              "description": "Hostname reported by the producing environment."
            },
            "execution_context": {
              "type": "string",
              "enum": [
                "native",
                "wsl",
                "container",
                "other"
              ],
              "description": "Normalized execution context classification for the producing environment."
            }
          }
        },
        "validation": {
          "type": "object",
          "description": "Inventory-wide validation metadata for external runtime surfaces relevant to downstream processing.",
          "required": [
            "lualatex"
          ],
          "additionalProperties": false,
          "properties": {
            "lualatex": {
              "$ref": "#/$defs/lualatex_validation_metadata",
              "description": "Inventory-level LaTeX runtime metadata describing the LuaLaTeX environment associated with validation and loadability decisions."
            }
          }
        }
      }
    },
    "fonts": {
      "type": "array",
      "description": "List of normalized per-face font entries contained in the inventory.",
      "items": {
        "$ref": "#/$defs/font_entry"
      }
    }
  },
  "$defs": {
    "font_entry": {
      "type": "object",
      "description": "Canonical per-face inventory entry containing identity, metrics, enrichment, typography, and validation state.",
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
        "metrics",
        "coverage",
        "inference",
        "charset",
        "typography",
        "loadability"
      ],
      "properties": {
        "path": {
          "type": "string",
          "minLength": 1,
          "description": "Canonical font file path. Multiple faces in the same file share this path."
        },
        "family": {
          "type": "string",
          "minLength": 1,
          "description": "Canonical family name associated with the font face."
        },
        "subfamily": {
          "type": "string",
          "minLength": 1,
          "description": "Style or face name reported for the font entry."
        },
        "typographic_subfamily": {
          "type": [
            "string",
            "null"
          ],
          "description": "Typographic subfamily name when available, otherwise null."
        },
        "full_name": {
          "type": "string",
          "minLength": 1,
          "description": "Human-readable full font face name."
        },
        "postscript_name": {
          "type": "string",
          "minLength": 1,
          "description": "PostScript face name used for stable font identification."
        },
        "version_string": {
          "type": "string",
          "minLength": 1,
          "description": "Version string extracted from the font metadata."
        },
        "unique_font_id": {
          "type": "string",
          "minLength": 1,
          "description": "Deterministic Fontshow identifier for the font face."
        },
        "metrics": {
          "$ref": "#/$defs/metrics",
          "description": "Normalized technical metrics and numeric font properties."
        },
        "coverage": {
          "type": "object",
          "additionalProperties": true,
          "description": "Coverage and Unicode-derived enrichment data associated with the font."
        },
        "inference": {
          "type": "object",
          "additionalProperties": true,
          "description": "Inference outputs derived from coverage, charset, and language processing."
        },
        "charset": {
          "type": "object",
          "additionalProperties": true,
          "description": "Charset-oriented raw or normalized data retained for downstream analysis."
        },
        "typography": {
          "$ref": "#/$defs/typography",
          "description": "Typography-oriented rendering metadata, specimens, and render-policy fields."
        },
        "loadability": {
          "$ref": "#/$defs/loadability",
          "description": "Per-font persisted loadability state for external rendering engines."
        },
        "warnings": {
          "type": "array",
          "description": "Structured warnings attached to the font entry during inventory generation or enrichment.",
          "items": {
            "$ref": "#/$defs/warning"
          }
        }
      }
    },
    "metrics": {
      "type": "object",
      "description": "Normalized numeric metrics and technical font properties used for diagnostics and downstream policy decisions.",
      "required": [
        "units_per_em",
        "ascent",
        "descent",
        "weight_class",
        "width_class",
        "italic_angle",
        "is_fixed_pitch",
        "glyph_count"
      ],
      "additionalProperties": false,
      "properties": {
        "units_per_em": {
          "type": "integer",
          "minimum": 1,
          "description": "Units-per-em value reported by the font."
        },
        "ascent": {
          "type": "integer",
          "description": "Ascent metric reported by the font."
        },
        "descent": {
          "type": "integer",
          "description": "Descent metric reported by the font."
        },
        "weight_class": {
          "type": "integer",
          "minimum": 1,
          "maximum": 1000,
          "description": "Normalized OS/2 weight class value."
        },
        "width_class": {
          "type": "integer",
          "minimum": 1,
          "maximum": 9,
          "description": "Normalized OS/2 width class value."
        },
        "italic_angle": {
          "type": "number",
          "description": "Italic angle reported by the font."
        },
        "is_fixed_pitch": {
          "type": "boolean",
          "description": "Whether the font is reported as fixed-pitch or monospaced."
        },
        "glyph_count": {
          "type": "integer",
          "minimum": 1,
          "description": "Number of glyphs reported by the font."
        }
      }
    },
    "typography": {
      "type": "object",
      "description": "Typography-oriented fields used for specimen generation, script labeling, and render-policy selection.",
      "required": [
        "sample_text",
        "specimen_text",
        "specimen_strategy",
        "specimen_glyph_count",
        "primary_script",
        "script_display_name",
        "render_policy",
        "script_source"
      ],
      "additionalProperties": false,
      "properties": {
        "sample_text": {
          "type": "object",
          "description": "Embedded sample text extracted from the font itself.",
          "required": [
            "source",
            "text"
          ],
          "additionalProperties": false,
          "properties": {
            "source": {
              "type": "string",
              "const": "font",
              "description": "Provenance label for the embedded sample text."
            },
            "text": {
              "type": "string",
              "description": "Sample text extracted from the font, which may be empty when no embedded sample is available."
            }
          }
        },
        "specimen_text": {
          "type": "string",
          "minLength": 1,
          "description": "Final deterministic specimen text chosen for rendering and validation."
        },
        "specimen_strategy": {
          "type": "string",
          "description": "Strategy that produced the final specimen text.",
          "enum": [
            "internal",
            "script",
            "language",
            "pua",
            "cmap",
            "deferred",
            "validated-language-sample",
            "validated-fallback"
          ]
        },
        "specimen_glyph_count": {
          "type": [
            "integer",
            "null"
          ],
          "minimum": 1,
          "description": "Count of accepted base glyphs in the final specimen text."
        },
        "specimen_rejection_reason": {
          "type": [
            "string",
            "null"
          ],
          "description": "Structured rejection or fallback reason recorded during specimen generation."
        },
        "primary_script": {
          "type": [
            "string",
            "null"
          ],
          "description": "Primary script code selected for the font, when one is available."
        },
        "script_display_name": {
          "type": [
            "string",
            "null"
          ],
          "description": "Human-readable display label associated with the primary script."
        },
        "render_policy": {
          "type": "object",
          "description": "LaTeX-oriented render-policy values derived from the selected script.",
          "required": [
            "polyglossia_language",
            "fontspec_opts"
          ],
          "additionalProperties": false,
          "properties": {
            "polyglossia_language": {
              "type": [
                "string",
                "null"
              ],
              "description": "Polyglossia language identifier associated with the selected script, when applicable."
            },
            "fontspec_opts": {
              "type": [
                "string",
                "null"
              ],
              "description": "fontspec option fragment associated with the selected script, when applicable."
            }
          }
        },
        "script_source": {
          "type": [
            "string",
            "null"
          ],
          "description": "Source from which the primary script decision was derived."
        },
        "opentype_features": {
          "type": "array",
          "description": "Reported OpenType feature tags preserved for typography-oriented inspection.",
          "items": {
            "type": "string"
          }
        }
      }
    },
    "loadability": {
      "type": "object",
      "description": "Per-font persisted loadability state for external engines that may reject or constrain rendering.",
      "required": [
        "lualatex"
      ],
      "additionalProperties": false,
      "properties": {
        "lualatex": {
          "type": "object",
          "description": "Persisted LuaLaTeX loadability result for the current font entry.",
          "required": [
            "attempted",
            "loadable",
            "reason",
            "runtime_fingerprint",
            "probe_input",
            "render_variants"
          ],
          "additionalProperties": false,
          "properties": {
            "attempted": {
              "type": "boolean",
              "description": "Whether LuaLaTeX loadability probing has been attempted for this font."
            },
            "loadable": {
              "type": [
                "boolean",
                "null"
              ],
              "description": "Persisted LuaLaTeX loadability result when probing has produced a definitive outcome."
            },
            "reason": {
              "type": [
                "string",
                "null"
              ],
              "description": "Deterministic short reason or failure summary associated with the persisted loadability state."
            },
            "runtime_fingerprint": {
              "type": [
                "string",
                "null"
              ],
              "description": "Runtime fingerprint under which the per-font loadability result was computed."
            },
            "probe_input": {
              "type": [
                "string",
                "null"
              ],
              "description": "Serialized probe input or probe-selection hint associated with the persisted validation attempt."
            },
            "render_variants": {
              "type": "array",
              "description": "Per-render-path LuaLaTeX validation results derived after parse-time script and render-policy enrichment.",
              "items": {
                "type": "object",
                "required": [
                  "script",
                  "fontspec_opts",
                  "attempted",
                  "loadable",
                  "reason",
                  "runtime_fingerprint",
                  "probe_input",
                  "specimen_text",
                  "specimen_glyph_count",
                  "specimen_strategy"
                ],
                "additionalProperties": false,
                "properties": {
                  "script": {
                    "type": "string",
                    "description": "ISO-15924 script code for the validated render path."
                  },
                  "fontspec_opts": {
                    "type": [
                      "string",
                      "null"
                    ],
                    "description": "Resolved fontspec option string used for the validated render path."
                  },
                  "attempted": {
                    "type": "boolean",
                    "description": "Whether LuaLaTeX validation was attempted for this render path."
                  },
                  "loadable": {
                    "type": [
                      "boolean",
                      "null"
                    ],
                    "description": "Persisted LuaLaTeX result for this render path."
                  },
                  "reason": {
                    "type": [
                      "string",
                      "null"
                    ],
                    "description": "Deterministic short reason or failure summary for this render path."
                  },
                  "runtime_fingerprint": {
                    "type": [
                      "string",
                      "null"
                    ],
                    "description": "Runtime fingerprint under which this render-path result was computed."
                  },
                  "probe_input": {
                    "type": [
                      "string",
                      "null"
                    ],
                    "description": "Serialized probe input or probe-selection hint associated with this render-path validation attempt."
                  },
                  "specimen_text": {
                    "type": [
                      "string",
                      "null"
                    ],
                    "description": "Validated specimen text that succeeded or was attempted for this render path."
                  },
                  "specimen_glyph_count": {
                    "type": [
                      "integer",
                      "null"
                    ],
                    "minimum": 0,
                    "description": "Accepted base-glyph count for the persisted render-variant specimen."
                  },
                  "specimen_strategy": {
                    "type": [
                      "string",
                      "null"
                    ],
                    "description": "Deterministic strategy label describing how the persisted render-variant specimen was produced."
                  }
                }
              }
            }
          }
        }
      }
    },
    "lualatex_validation_metadata": {
      "type": "object",
      "description": "Inventory-level metadata describing the LuaLaTeX-related program surface used for validation and loadability decisions.",
      "required": [
        "attempted",
        "engine",
        "engine_version",
        "luaotfload_version",
        "fontspec_version",
        "polyglossia_version",
        "runtime_fingerprint",
        "render_policy_version"
      ],
      "additionalProperties": false,
      "properties": {
        "attempted": {
          "type": "boolean",
          "description": "Whether inventory-wide LuaLaTeX validation or probing has been attempted."
        },
        "engine": {
          "type": [
            "string",
            "null"
          ],
          "description": "Name of the LaTeX engine associated with the validation metadata."
        },
        "engine_version": {
          "type": [
            "string",
            "null"
          ],
          "description": "Version string reported by the LaTeX engine."
        },
        "texlive_version": {
          "type": [
            "string",
            "null"
          ],
          "description": "TeX Live release identifier reported by the associated LaTeX runtime, when available."
        },
        "luaotfload_version": {
          "type": [
            "string",
            "null"
          ],
          "description": "Version of the luaotfload package available in the associated LaTeX runtime."
        },
        "fontspec_version": {
          "type": [
            "string",
            "null"
          ],
          "description": "Version of the fontspec package available in the associated LaTeX runtime."
        },
        "polyglossia_version": {
          "type": [
            "string",
            "null"
          ],
          "description": "Version of the Polyglossia package available in the associated LaTeX runtime."
        },
        "runtime_fingerprint": {
          "type": [
            "string",
            "null"
          ],
          "description": "Stable fingerprint of the relevant LaTeX runtime surface."
        },
        "render_policy_version": {
          "type": [
            "string",
            "null"
          ],
          "description": "Version or fingerprint of the render-policy inputs associated with validation."
        }
      }
    },
    "warning": {
      "type": "object",
      "description": "Structured warning record attached to an inventory font entry.",
      "required": [
        "code",
        "message",
        "severity"
      ],
      "additionalProperties": false,
      "properties": {
        "code": {
          "type": "string",
          "minLength": 1,
          "description": "Machine-readable warning code."
        },
        "message": {
          "type": "string",
          "minLength": 1,
          "description": "Human-readable warning message."
        },
        "severity": {
          "type": "string",
          "enum": [
            "info",
            "warning",
            "error"
          ],
          "description": "Normalized warning severity."
        }
      }
    }
  }
}
```

<!-- SCHEMA_JSON_END -->

## Related

- `docs/schema/index.md`
- `src/fontshow/schema/inventory_v1_5.json`
