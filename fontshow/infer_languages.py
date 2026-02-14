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
    Return the coverage ratio for a Unicode block.

    If the block size is unknown or zero, return 0.0.
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

    This function operates exclusively on Unicode-derived coverage data
    (e.g. unicode_blocks) and does NOT consume FontConfig charset metadata
    or any external language declarations.

    The returned mapping represents candidate languages along with
    supporting evidence, not definitive classification.

    Args:
        coverage: Unicode coverage metadata (e.g. font_entry["coverage"]).
        policy: Language inference policy selector.

    Returns:
        A mapping of language tags to inference evidence.
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

        # All required blocks must be present with sufficient coverage
        failed = False
        for block in required:
            ratio = _block_coverage_ratio(
                block_name=block,
                block_coverage=unicode_blocks,
                block_sizes=UNICODE_BLOCK_SIZES,
            )
            if ratio < LANGUAGE_BLOCK_COVERAGE_THRESHOLD:
                log_trace_cat(
                    log,
                    "infer",
                    "language candidate rejected",
                    extra={
                        "lang": lang,
                        "block": block,
                        "ratio": ratio,
                        "threshold": LANGUAGE_BLOCK_COVERAGE_THRESHOLD,
                        "covered": unicode_blocks.get(block, 0),
                        "size": UNICODE_BLOCK_SIZES.get(block, 0),
                    },
                )
                failed = True
                break

        if failed:
            continue

        evidence = sorted(required & unicode_blocks.keys())
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

    return inferred
