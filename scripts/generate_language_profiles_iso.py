#!/usr/bin/env python3
"""
Generate static LANGUAGE_PROFILES_ISO table.

Converts human-readable script names in LANGUAGE_PROFILES
to canonical ScriptISO codes using SCRIPT_HUMAN_TO_ISO.

Usage:
    python scripts/generate_language_profiles_iso.py
"""

from __future__ import annotations

from fontshow.language_tables import LANGUAGE_PROFILES, SCRIPT_HUMAN_TO_ISO


def main() -> None:
    print("LANGUAGE_PROFILES_ISO: dict[str, LanguageProfileISO] = {")

    for lang in sorted(LANGUAGE_PROFILES):
        profile = LANGUAGE_PROFILES[lang]

        scripts = [
            f'ScriptISO("{str(SCRIPT_HUMAN_TO_ISO[s]).upper()}")'
            for s in profile["scripts"]
        ]

        print(f'    "{lang}": {{')

        # Copy all fields except scripts
        for key, value in profile.items():
            if key == "scripts":
                continue
            print(f'        "{key}": {value!r},')

        print(f'        "scripts": [{", ".join(scripts)}],')

        print("    },")

    print("}")


if __name__ == "__main__":
    main()
