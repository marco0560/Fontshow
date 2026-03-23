# Unicode Data Snapshot (Vendored)

This directory contains vendored data files from the Unicode Character Database (UCD).

## Purpose

Fontshow derives script and language inference tables from authoritative
Unicode sources. These files are vendored to guarantee:

* deterministic builds
* offline reproducibility
* stable inference behavior
* auditability of Unicode assumptions

## Source

Unicode Character Database (UCD)
[https://www.unicode.org/Public/17.0.0/ucd/](https://www.unicode.org/Public/17.0.0/ucd/)

## Files

* Blocks-17.0.0.txt
* Scripts-17.0.0.txt

## Unicode Version

17.0.0

## Regeneration

These files MUST NOT be edited manually.

To update Unicode version:

1. Download new UCD release files.
2. Replace files in this directory.
3. Regenerate derived tables using:
   python scripts/generate_unicode_tables.py
4. Run full test suite.

## License

Unicode® data files are © Unicode, Inc.
Distributed under Unicode Terms of Use:
[https://www.unicode.org/terms_of_use.html](https://www.unicode.org/terms_of_use.html)
