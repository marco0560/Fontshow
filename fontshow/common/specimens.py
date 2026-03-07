"""
Shared specimen selectors.

This module contains deterministic helpers for selecting
language samples from the ontology.
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
