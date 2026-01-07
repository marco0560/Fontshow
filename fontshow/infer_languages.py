# fontshow/infer_languages.py
"""
Language inference based on Unicode coverage metadata.

This module infers candidate languages exclusively from Unicode block coverage
data produced during the raw inventory stage.

FontConfig-derived charset metadata is NOT consumed by this module and does not
influence language inference.
"""

from __future__ import annotations

from typing import Any

Confidence = str  # "low" | "medium" | "high"

LANGUAGE_PROFILES: dict[str, dict[str, Any]] = {
    # Latin
    "en": {
        "scripts": ["Latin"],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement"],
    },
    "fr": {
        "scripts": ["Latin"],
        "required_blocks": ["Basic Latin", "Latin-1 Supplement"],
        "optional_blocks": ["Latin Extended-A"],
    },
    "de": {
        "scripts": ["Latin"],
        "required_blocks": ["Basic Latin", "Latin-1 Supplement"],
        "optional_blocks": ["Latin Extended-A"],
    },
    # Cyrillic
    "ru": {
        "scripts": ["Cyrillic"],
        "required_blocks": ["Cyrillic"],
        "optional_blocks": ["Cyrillic Supplement"],
    },
    # Greek
    "el": {
        "scripts": ["Greek"],
        "required_blocks": ["Greek and Coptic"],
        "optional_blocks": [],
    },
    # Arabic
    "ar": {
        "scripts": ["Arabic"],
        "required_blocks": ["Arabic"],
        "optional_blocks": ["Arabic Supplement"],
    },
    # CJK (permissivo by design)
    "zh": {
        "scripts": ["Han"],
        "required_blocks": ["CJK Unified Ideographs"],
        "optional_blocks": [],
    },
    "ja": {
        "scripts": ["Han", "Hiragana", "Katakana"],
        "required_blocks": ["Hiragana", "Katakana"],
        "optional_blocks": ["CJK Unified Ideographs"],
    },
}


def infer_languages(
    coverage: dict[str, Any],
    policy: str = "permissive",
) -> dict[str, dict[str, Any]]:
    """
    Infer candidate languages from Unicode coverage metadata.

    This function operates exclusively on Unicode-derived coverage data
    (e.g. unicode_blocks) and does NOT consume FontConfig charset metadata
    or any external language declarations.

    The returned mapping represents candidate languages along with
    supporting evidence, not definitive classification.

    Args:
        coverage: Unicode coverage metadata extracted from the raw inventory.
        policy: Language inference policy selector.

    Returns:
        A mapping of language tags to inference evidence.
    """

    unicode_blocks: set[str] = set(coverage.get("unicode_blocks", []))

    inferred: dict[str, dict[str, Any]] = {}

    for lang, profile in LANGUAGE_PROFILES.items():
        required = set(profile["required_blocks"])
        optional = set(profile.get("optional_blocks", []))

        if not required.issubset(unicode_blocks):
            continue

        evidence = sorted(required & unicode_blocks)
        optional_hits = sorted(optional & unicode_blocks)

        if optional_hits:
            confidence: Confidence = "high"
            evidence.extend(optional_hits)
        else:
            confidence = "medium"

        inferred[lang] = {
            "confidence": confidence,
            "evidence": evidence,
        }

    return inferred
