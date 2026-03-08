"""
Shared specimen selection helpers.

This module provides deterministic utilities for selecting representative
text samples used when rendering font specimens.

Responsibilities
----------------
- Select a representative language sample based on inferred languages.
- Provide fallback samples derived from script metadata when languages
  are unavailable.
- Ensure specimen selection is deterministic across runs.

Design principles
-----------------
Sample selection operates exclusively on normalized language and script
metadata derived from the ontology tables. No rendering or formatting
logic is implemented here.

Architectural role
------------------
This module belongs to the **shared utilities layer** and provides
specimen-selection helpers used by the catalog rendering subsystem.
"""

from __future__ import annotations

from fontshow.core.types import tag_to_iso
from fontshow.ontology.language_tables import LANGUAGE_INFO, SCRIPT_INFO


def choose_language_sample(
    languages: list[str] | None,
    scripts: list[str] | None = None,
) -> str | None:
    """
    Choose a deterministic language-aware sample text.

    Priority
    --------
    1. Sample from inferred languages
    2. Representative language from dominant script
    """

    # ---------------------------------------------------------
    # 1. Use inferred languages
    # ---------------------------------------------------------

    if languages:
        for lang in languages:
            info = LANGUAGE_INFO.get(lang)
            if isinstance(info, dict):
                sample = info.get("sample")
                if isinstance(sample, str) and sample:
                    return sample

    # ---------------------------------------------------------
    # 2. Script fallback
    # ---------------------------------------------------------

    if scripts:
        script_iso = tag_to_iso(scripts[0])
        script_info = SCRIPT_INFO.get(script_iso)

        if isinstance(script_info, dict):
            fallback_lang = script_info.get("display_language")

            if isinstance(fallback_lang, str):
                lang_info = LANGUAGE_INFO.get(fallback_lang)

                if isinstance(lang_info, dict):
                    sample = lang_info.get("sample")
                    if isinstance(sample, str) and sample:
                        return sample

    return None
