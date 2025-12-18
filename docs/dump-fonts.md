# dump_fonts.py

`dump_fonts.py` generates a *canonical* font inventory for Fontshow.

The goal is to make the rest of the pipeline OS-agnostic:

- **Dump phase (OS-specific):** discover installed fonts and extract metadata
- **Parsing / rendering (OS-agnostic):** consume a stable JSON schema

## Output

By default, the script writes:

- `font_inventory.json`

The JSON follows the schema described in `docs/font-inventory-schema.md`.

## Requirements

### Common

- Python 3.10+
- `fontTools` (strongly recommended)

### Linux

- `fontconfig` (`fc-list`, `fc-query`) for discovery and enrichment

### Windows

- Uses Windows Registry + Fonts directories for discovery
- No FontConfig is required

## Installation notes

### Linux (Gentoo)

Install fontTools via Portage:

    sudo emerge dev-python/fonttools

To add WOFF2 support (recommended):

    echo "dev-python/fonttools brotli" | sudo tee /etc/portage/package.use/fonttools
    sudo emerge --changed-use dev-python/fonttools

### Windows

In a virtual environment:

    pip install fonttools

(Use a pinned version if you want reproducible inventories.)

## Usage

Basic:

    python3 scripts/dump_fonts.py --output font_inventory.json

Disable cache:

    python3 scripts/dump_fonts.py --no-cache

Linux only: skip FontConfig enrichment:

    python3 scripts/dump_fonts.py --no-fontconfig

Linux only: include the FontConfig charset block (large output):

    python3 scripts/dump_fonts.py --include-charset

Strict mode (abort on errors):

    python3 scripts/dump_fonts.py --strict

## Caching

The script caches per-font `fontTools` results under:

- `.font_cache/`

The cache key depends on:

- file path
- file size
- modification time

Cache is automatically invalidated when the file changes.

## Design notes

- Windows inventory will usually have empty `languages/scripts/charset` fields
  because those are typically derived from FontConfig.
- Most OpenType/TrueType metadata is extracted with `fontTools` and is
  cross-platform.
