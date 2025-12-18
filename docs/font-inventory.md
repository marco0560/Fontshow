# Font Inventory Script

This repository includes a Python script (`dump_fonts_fc.py`) for advanced analysis
of fonts installed on a Linux system.

## Main features

- Enumeration of installed fonts via `fontconfig` (`fc-list`)
- Full metadata extraction using `fc-query`
- Advanced OpenType / TrueType inspection via `fontTools`
- Detection of font containers:
  - TrueType
  - OpenType
  - WOFF
  - WOFF2
- Persistent on-disk caching to avoid repeated analysis
- Structured, human-readable output suitable for further processing

## Dependencies

### Runtime requirements

- Linux system with `fontconfig`
  - `fc-list`
  - `fc-query`
- Python ≥ 3.10

### Python dependencies

- `fonttools` (optional but strongly recommended)

On Gentoo:

    sudo emerge dev-python/fonttools

To enable full WOFF2 support:

    echo "dev-python/fonttools brotli" | sudo tee /etc/portage/package.use/fonttools
    sudo emerge --changed-use dev-python/fonttools

## Cache behavior

The script uses a persistent cache directory:

    .font_cache/

Cache entries are automatically invalidated when:
- the font file changes
- the file size changes
- the modification timestamp changes

This applies to both `fc-query` output and `fontTools` analysis.

## Usage

Run the script with:

    python3 dump_fonts_fc.py

The output file generated is:

    font_inventory.txt

## Notes

- WOFF and WOFF2 are compressed containers mainly used for web fonts.
- If `fontTools` (or Brotli support) is not available, advanced analysis is skipped.
- The script is read-only and does not modify the system.
