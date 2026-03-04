#!/usr/bin/env python3
"""
Generate a static SCRIPT_RENDER_POLICY table.

This script reads the ontology tables defined in
fontshow.language_tables and emits a Python literal
table suitable for direct inclusion in language_tables.py.

Usage
-----

    python scripts/generate_script_render_policy.py

Output is printed to stdout.
"""

from __future__ import annotations

from fontshow.language_tables import (
    RTL_LANGUAGES,
    SCRIPT_ISO_TO_POLYGLOSSIA,
)
from fontshow.types import ScriptISO, ScriptRenderPolicy


def build_table() -> dict[ScriptISO, ScriptRenderPolicy]:
    table: dict[ScriptISO, ScriptRenderPolicy] = {}

    for script, (lang, opts) in sorted(SCRIPT_ISO_TO_POLYGLOSSIA.items()):
        table[script] = ScriptRenderPolicy(
            language=lang,
            fontspec_opts=opts,
            rtl=lang in RTL_LANGUAGES,
            requires_polyglossia=bool(lang),
        )

    return table


def emit_table(table: dict[ScriptISO, ScriptRenderPolicy]) -> None:
    print("SCRIPT_RENDER_POLICY: dict[ScriptISO, ScriptRenderPolicy] = {")
    for script, policy in table.items():
        script_name = str(script).title()
        print(f'    ScriptISO("{script_name}"): ScriptRenderPolicy(')
        print(f'        language="{policy.language}",')
        print(f'        fontspec_opts="{policy.fontspec_opts}",')
        print(f"        rtl={policy.rtl},")
        print(f"        requires_polyglossia={policy.requires_polyglossia},")
        print("    ),")
    print("}")


def main() -> None:
    table = build_table()
    emit_table(table)


if __name__ == "__main__":
    main()
