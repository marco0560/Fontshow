# Font inventory JSON schema

This document describes the canonical JSON produced by `scripts/dump_fonts.py`.

## Top-level object

```json
{
  "metadata": { "...": "..." },
  "fonts": [ { "identity": {...}, "...": "..." } ]
}
```

### metadata

- `generator`: string identifying the generator
- `platform`: `linux` or `windows`
- `generated_at`: ISO-8601 UTC timestamp
- `python`: Python version string
- `fontconfig`: (Linux only) reported `fc-list --version` output, if available

### fonts

Array of **FontDescriptor** objects.

## FontDescriptor

### identity

- `file`: full path to the font file
- `family`: best-effort family name (from OpenType name table)
- `style`: best-effort subfamily/style name (from OpenType name table)
- `postscript_name`: best-effort PostScript name (name ID 6)

### format

- `container`: `TrueType`, `OpenType`, `WOFF`, `WOFF2`, `TTC`, `Unknown`
- `font_type`: `TrueType`, `OpenType CFF`, `Unknown`
- `variable`: boolean (best-effort)
- `color`: boolean (best-effort)

### coverage

- `unicode.count`: number of Unicode codepoints in the cmap
- `unicode.min`: minimum codepoint (`U+....`)
- `unicode.max`: maximum codepoint (`U+....`)
- `scripts`: list of OpenType script tags (Linux + FontConfig only)
- `languages`: list of language tags (Linux + FontConfig only)
- `charset`: optional raw FontConfig charset block (Linux only, if enabled)

### typography

- `weight_class`: integer (OS/2 usWeightClass) or null
- `width_class`: integer (OS/2 usWidthClass) or null
- `opentype_features`: list of OpenType feature tags, derived from GSUB/GPOS

### classification

Best-effort flags useful for rendering decisions:

- `is_text`
- `is_decorative`
- `is_emoji`

### license

- `vendor`: OS/2 vendor id, if available
- `embedding_rights`: OS/2 fsType, if available
- `text`: license text (name ID 13), if available
- `url`: license URL (name ID 14), if available

### sources

- `fonttools`: boolean
- `fontconfig`: boolean
- `windows_registry`: boolean
- optional `fonttools_error` may appear if fontTools extraction failed
