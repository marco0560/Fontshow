#!/usr/bin/env python3
"""
Generate static SCRIPT_ISO_SAMPLES table.

Reads SCRIPT_SAMPLES and SCRIPT_HUMAN_TO_ISO from
fontshow.language_tables and emits a Python literal table.

Usage:
    python scripts/generate_script_iso_samples.py
"""

from __future__ import annotations

from fontshow.language_tables import SCRIPT_HUMAN_TO_ISO, SCRIPT_SAMPLES


def main() -> None:
    pairs_by_iso: dict[str, tuple[str, str]] = {}

    # Per-ISO preferred human keys (higher priority first)
    preferred_names: dict[str, list[str]] = {
        "HANI": ["CJK", "Han"],
    }

    for name, sample in SCRIPT_SAMPLES.items():
        iso = SCRIPT_HUMAN_TO_ISO[name]
        iso_key = str(iso).upper()

        # If we haven't picked a sample for this ISO yet, take it.
        if iso_key not in pairs_by_iso:
            pairs_by_iso[iso_key] = (name, sample)
            continue

        # Otherwise, possibly replace based on preference order.
        pref = preferred_names.get(iso_key)
        if pref is None:
            continue

        current_name, _current_sample = pairs_by_iso[iso_key]

        try:
            new_rank = pref.index(name)
        except ValueError:
            new_rank = len(pref)

        try:
            current_rank = pref.index(current_name)
        except ValueError:
            current_rank = len(pref)

        if new_rank < current_rank:
            pairs_by_iso[iso_key] = (name, sample)

    pairs: list[tuple[str, str]] = [
        (iso_key, sample) for iso_key, (_name, sample) in pairs_by_iso.items()
    ]
    pairs.sort(key=lambda kv: kv[0])

    print("SCRIPT_ISO_SAMPLES: dict[ScriptISO, str] = {")
    for iso_key, sample in pairs:
        print(f'    ScriptISO("{iso_key}"): {sample!r},')
    print("}")


if __name__ == "__main__":
    main()
