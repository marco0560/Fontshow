# fontshow/infer_languages.py
"""
fontshow.infer_languages
=======================

Language inference module for Fontshow.

This module provides deterministic and explainable inference of
human languages supported by a font, based solely on Unicode
coverage metadata.

Design goals:
- No heuristics based on font names
- No NLP or statistical models
- Fully explainable results (confidence + evidence)
- Reusable across inventory parsing, catalog generation and future APIs

Introduced in: C4.3
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
    Infer supported human languages from Unicode coverage metadata.

    This function analyzes the Unicode blocks covered by a font and
    matches them against predefined language profiles.

    The inference is deterministic and explainable:
    each inferred language is returned together with a confidence level
    and the Unicode blocks that justified the inference.

    Parameters
    ----------
    coverage : dict[str, Any]
        Unicode coverage metadata for a font.
        Expected to contain a ``unicode_blocks`` key with a list of
        Unicode block names.

    policy : str, optional
        Inference policy.
        Currently supported:
        - ``"permissive"``: infer a language as soon as all required
          blocks are present (default).

    Returns
    -------
    dict[str, dict[str, Any]]
        Mapping from ISO language code to inference metadata.

        Example::

            {
                "fr": {
                    "confidence": "high",
                    "evidence": [
                        "Basic Latin",
                        "Latin-1 Supplement",
                        "Latin Extended-A"
                    ]
                }
            }

    Notes
    -----
    - No language is inferred if required Unicode blocks are missing.
    - Confidence levels are qualitative and not probabilistic.
    - This function does not modify its input.

    Introduced in
    -------------
    C4.3
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
