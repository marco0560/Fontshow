# Advanced font analysis (fontTools integration)

The `dump_fonts_fc.py` script includes an advanced font analysis layer based on
[`fontTools`](https://github.com/fonttools/fonttools), providing deep inspection
of OpenType / TrueType fonts beyond what `fontconfig` exposes.

## Supported font containers

The script detects and correctly handles the following font containers:

- TrueType (`.ttf`)
- OpenType (`.otf`)
- Web Open Font Format (`.woff`)
- Web Open Font Format 2 (`.woff2`)

WOFF and WOFF2 are compressed containers primarily used for web fonts.
Internally, they still contain standard OpenType or TrueType data.
WOFF2 requires Brotli support to be fully parsed.

## Caching strategy

To avoid repeated and expensive font parsing, the script implements a persistent
on-disk cache:

- Cache directory: `.font_cache/`
- Cache key: font path + modification time + file size
- Cache is automatically invalidated when the font file changes

This applies to both `fc-query` output and `fontTools` analysis.

## OpenType / TrueType metadata extraction

When `fontTools` is available, the script extracts:

- Container format (TrueType, OpenType, WOFF, WOFF2)
- Internal font type (glyf / CFF)
- List of available OpenType tables
- Name table entries (family, style, full name, PostScript name, version, etc.)
- Unicode coverage (number of codepoints, min/max range)
- Variable font support (`fvar`, `STAT`, `avar`, `gvar`)
- OpenType layout features (GSUB / GPOS)
- OS/2 metrics (weight class, width class, vendor ID), when readable

## Robust error handling

Some fonts in the wild contain malformed or truncated OpenType tables.
To ensure the script never fails hard:

- Each non-essential table is accessed defensively
- Malformed tables (e.g. `OS/2`) are skipped and reported as errors
- Analysis continues for the remaining font data

Example error report:

    "os2": {
      "error": "OS/2 table unreadable: unpack requires a buffer of 22 bytes"
    }

This approach makes the script suitable for large-scale font inventories
and real-world font collections.

## Optional dependencies

To enable advanced OpenType analysis, install:

- `dev-python/fonttools`

For full WOFF2 support (recommended):

- `dev-python/fonttools` with the `brotli` USE flag enabled

On Gentoo:

    sudo emerge dev-python/fonttools

    echo "dev-python/fonttools brotli" | sudo tee /etc/portage/package.use/fonttools
    sudo emerge --changed-use dev-python/fonttools

If `fontTools` is not available, the script gracefully falls back to
`fontconfig`-only analysis.
