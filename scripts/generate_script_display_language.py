#!/usr/bin/env python3
"""
Generate a static SCRIPT_ISO_TO_DISPLAY_LANGUAGE table.

This script reads SCRIPT_TO_DISPLAY_LANGUAGE from fontshow.language_tables
and emits a Python literal dictionary suitable for direct inclusion in
fontshow/language_tables.py.

Usage:
    python scripts/generate_script_display_language.py

Output is printed to stdout.
"""

from __future__ import annotations

from fontshow.language_tables import SCRIPT_TO_DISPLAY_LANGUAGE
from fontshow.types import ScriptISO, tag_to_iso


def main() -> None:
    pairs: list[tuple[ScriptISO, str]] = []
    for tag, lang in SCRIPT_TO_DISPLAY_LANGUAGE.items():
        pairs.append((tag_to_iso(tag), lang))

    pairs.sort(key=lambda kv: str(kv[0]))

    print("SCRIPT_ISO_TO_DISPLAY_LANGUAGE: dict[ScriptISO, str] = {")
    for iso, lang in pairs:
        iso_name = str(iso).upper()
        print(f'    ScriptISO("{iso_name}"): "{lang}",')
    print("}")


if __name__ == "__main__":
    main()
