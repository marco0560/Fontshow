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

from fontshow.logging_utils import log, log_trace_cat
from fontshow.types import Confidence, LanguageInferenceInfo

# Minimum fraction of a Unicode block that must be covered
# to infer a language from that block.
LANGUAGE_BLOCK_COVERAGE_THRESHOLD = 0.40

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
    # Georgian
    "ka": {
        "scripts": ["Georgian"],
        "required_blocks": ["Georgian"],
        "optional_blocks": ["Georgian Supplement"],
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
    # Cherokee
    "chr": {
        "scripts": ["Cherokee"],
        "required_blocks": ["Cherokee", "Cherokee Supplement"],
        "optional_blocks": [],
    },
    # Ethiopic
    "am": {
        "scripts": ["Ethiopic"],
        "required_blocks": ["Ethiopic"],
        "optional_blocks": ["Ethiopic Supplement", "Ethiopic Extended"],
    },
    # Indic / SE Asia
    "ta": {
        "scripts": ["Tamil"],
        "required_blocks": ["Tamil", "Tamil Supplement"],
        "optional_blocks": [],
    },
    "th": {
        "scripts": ["Thai"],
        "required_blocks": ["Thai"],
        "optional_blocks": [],
    },
    "lo": {
        "scripts": ["Lao"],
        "required_blocks": ["Lao"],
        "optional_blocks": [],
    },
    "my": {
        "scripts": ["Myanmar"],
        "required_blocks": ["Myanmar", "Myanmar Extended-A", "Myanmar Extended-B"],
        "optional_blocks": [],
    },
    # Yi
    "ii": {
        "scripts": ["Yi"],
        "required_blocks": ["Yi Syllables"],
        "optional_blocks": [],
    },
    # CJK (permissive by design)
    "zh": {
        "scripts": ["Han"],
        "required_blocks": ["CJK Unified Ideographs"],
        "optional_blocks": [],
    },
    "ja": {
        "scripts": ["Hiragana", "Katakana"],
        "required_blocks": ["Kana Supplement"],
        "optional_blocks": [
            "Hiragana",
            "Katakana",
            "Kana Extended-A",
            "CJK Unified Ideographs",
        ],
    },
}


# ------------------------------------------------------------------
# Canonical display language per ISO-15924 script
#
# Purpose:
# Fontshow needs a representative language for specimen rendering,
# not linguistic capability classification.
#
# This mapping provides a deterministic fallback when coverage-based
# inference yields no reliable languages.
# ------------------------------------------------------------------

SCRIPT_TO_DISPLAY_LANGUAGE: dict[str, str] = {
    "latn": "en",
    "grek": "el",
    "cyrl": "ru",
    "hebr": "he",
    "arab": "ar",
    "deva": "hi",
    "beng": "bn",
    "taml": "ta",
    "thai": "th",
    "laoo": "lo",
    "mymr": "my",
    "armn": "hy",
    "geor": "ka",
    "ethi": "ti",
    "cher": "chr",
    "khmr": "km",
    "bugi": "bug",
    "buhd": "bku",
    "yiii": "ii",
    "jpan": "ja",
    "hang": "ko",
    "hani": "zh",
}

# Normative Unicode block sizes (codepoint counts).
# This table is intentionally static and limited to blocks
# referenced by language profiles or commonly encountered.
UNICODE_BLOCK_SIZES: dict[str, int] = {
    # Latin
    "Basic Latin": 128,
    "Latin-1 Supplement": 128,
    "Latin Extended-A": 128,
    "Latin Extended-B": 208,
    "Latin Extended Additional": 256,
    # Greek
    "Greek and Coptic": 135,
    "Greek Extended": 256,
    # Cyrillic
    "Cyrillic": 256,
    "Cyrillic Supplement": 48,
    "Cyrillic Extended-A": 32,
    "Cyrillic Extended-B": 96,
    # Hebrew
    "Hebrew": 112,
    # Arabic
    "Arabic": 256,
    "Arabic Supplement": 48,
    "Arabic Extended-A": 96,
    # Indic - partial and common
    "Devanagari": 128,
    "Bengali": 128,
    "Gurmukhi": 128,
    "Gujarati": 128,
    "Oriya": 128,
    "Tamil": 128,
    "Telugu": 128,
    "Kannada": 128,
    "Malayalam": 128,
    # SE Asia / Yi
    "Thai": 128,
    "Lao": 128,
    "Myanmar": 160,
    "Yi Syllables": 1168,
    # East Asian (coarse-grained)
    "CJK Unified Ideographs": 20992,
    "CJK Unified Ideographs Extension A": 6592,
    "Hangul Syllables": 11172,
    "Hiragana": 96,
    "Katakana": 96,
    # Symbols (intentionally included for completeness)
    "General Punctuation": 112,
    "Currency Symbols": 48,
    "Letterlike Symbols": 80,
}


def _block_coverage_ratio(
    block_name: str,
    block_coverage: dict[str, int],
    block_sizes: dict[str, int],
) -> float:
    """
    Compute coverage ratio for a Unicode block.

    Parameters
    ----------
    block_name : str
        Name of the Unicode block.
    block_coverage : dict[str, int]
        Mapping of block names to covered codepoint counts.
    block_sizes : dict[str, int]
        Mapping of block names to normative block sizes.

    Returns
    -------
    float
        Fraction of the block covered (covered / size).
        Returns 0.0 if the block size is unknown or zero.
    """
    covered = block_coverage.get(block_name, 0)
    size = block_sizes.get(block_name, 0)

    if size <= 0:
        return 0.0

    return covered / size


def infer_languages(
    coverage: dict[str, Any],
    policy: str = "permissive",
) -> dict[str, LanguageInferenceInfo]:
    """
    Infer candidate languages from Unicode coverage metadata.

    Parameters
    ----------
    coverage : dict[str, Any]
        Unicode coverage metadata (e.g. font_entry["coverage"]).
    policy : str, optional
        Language inference policy selector.

    Returns
    -------
    dict[str, LanguageInferenceInfo]
        Mapping of language tags to inference evidence.

    Notes
    -----
    This function operates exclusively on Unicode-derived coverage data
    (e.g. unicode_blocks) and does NOT consume FontConfig charset metadata
    or any external language declarations.

    The returned mapping represents candidate languages supported by
    the font, along with supporting evidence, and is not a definitive
    classification.
    """
    log_trace_cat(
        log,
        "infer",
        "language inference started",
        extra={
            "policy": policy,
            "unicode_blocks_count": len(coverage.get("unicode_blocks", {}) or {}),
        },
    )

    unicode_blocks: dict[str, int] = coverage.get("unicode_blocks", {}) or {}

    inferred: dict[str, LanguageInferenceInfo] = {}

    for lang, profile in LANGUAGE_PROFILES.items():
        required = set(profile["required_blocks"])
        optional = set(profile.get("optional_blocks", []))

        # ------------------------------------------------------------------
        # Fontshow v1.2 permissive rule:
        # A language is accepted if ANY required block reaches threshold.
        # Real fonts frequently expose partial Unicode coverage.
        # ------------------------------------------------------------------
        passed_blocks: list[str] = []

        for block in required:
            ratio = _block_coverage_ratio(
                block_name=block,
                block_coverage=unicode_blocks,
                block_sizes=UNICODE_BLOCK_SIZES,
            )

            if ratio >= LANGUAGE_BLOCK_COVERAGE_THRESHOLD:
                passed_blocks.append(block)

        if not passed_blocks:
            log_trace_cat(
                log,
                "infer",
                "language candidate rejected",
                extra={
                    "lang": lang,
                    "reason": "no_required_block_passed",
                    "required_blocks": sorted(required),
                },
            )
            continue

        evidence = sorted(set(passed_blocks))
        optional_hits = sorted(optional & unicode_blocks.keys())

        confidence: Confidence = "medium"
        if optional_hits:
            confidence = "high"
            evidence.extend(optional_hits)

        log_trace_cat(
            log,
            "infer",
            "language candidate accepted",
            extra={
                "lang": lang,
                "confidence": confidence,
                "evidence_count": len(evidence),
                "required_blocks": sorted(required),
                "optional_hits": optional_hits,
                "evidence": evidence,
            },
        )

        inferred[lang] = LanguageInferenceInfo(
            confidence=confidence,
            evidence=evidence,
        )

    log_trace_cat(
        log,
        "infer",
        "language inference completed",
        extra={
            "policy": policy,
            "languages_inferred": len(inferred),
            "profiles_total": len(LANGUAGE_PROFILES),
        },
    )

    # -------------------------------------------------
    # Canonical language normalization
    # -------------------------------------------------

    if inferred:
        # Canonical Latin fallback rule
        unicode_blocks = coverage.get("unicode_blocks", {}) or {}
        blocks_present = set(unicode_blocks.keys())

        if blocks_present == {"Basic Latin"} and "en" in inferred:
            inferred = {"en": inferred["en"]}

    else:
        # Script-driven display fallback
        scripts = coverage.get("_inferred_scripts")
        if isinstance(scripts, list) and scripts:
            primary = str(scripts[0]).lower()
            lang = SCRIPT_TO_DISPLAY_LANGUAGE.get(primary) or ""
            if lang:
                inferred[lang] = LanguageInferenceInfo(
                    confidence="medium",
                    evidence=["script-default"],
                )

    return inferred
