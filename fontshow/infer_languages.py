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

from fontshow.language_tables import LANGUAGE_PRIMARY_SCRIPT
from fontshow.logging_utils import log, log_trace_cat
from fontshow.types import Confidence, LanguageInferenceInfo
from fontshow.unicode_tables import UNICODE_BLOCK_SIZES

# Minimum fraction of a Unicode block that must be covered
# to infer a language from that block.
LANGUAGE_BLOCK_COVERAGE_THRESHOLD = 0.40

LANGUAGE_PROFILES: dict[str, dict[str, Any]] = {
    # Arabic
    "ar": {
        "scripts": ["Arabic"],
        "required_blocks": ["Arabic"],
        "optional_blocks": ["Arabic Supplement"],
    },
    # Ethiopic
    "am": {
        "scripts": ["Ethiopic"],
        "required_blocks": ["Ethiopic"],
        "optional_blocks": ["Ethiopic Supplement", "Ethiopic Extended"],
    },
    # Cherokee
    "chr": {
        "scripts": ["Cherokee"],
        "required_blocks": ["Cherokee", "Cherokee Supplement"],
        "optional_blocks": [],
    },
    # German
    "de": {
        "scripts": ["Latin"],
        "required_blocks": ["Basic Latin", "Latin-1 Supplement"],
        "optional_blocks": ["Latin Extended-A"],
    },
    # Greek
    "el": {
        "scripts": ["Greek"],
        "required_blocks": ["Greek and Coptic"],
        "optional_blocks": [],
    },
    # English
    "en": {
        "scripts": ["Latin"],
        "required_blocks": ["Basic Latin"],
        "optional_blocks": ["Latin-1 Supplement"],
    },
    # French
    "fr": {
        "scripts": ["Latin"],
        "required_blocks": ["Basic Latin", "Latin-1 Supplement"],
        "optional_blocks": ["Latin Extended-A"],
    },
    # Yi
    "ii": {
        "scripts": ["Yi"],
        "required_blocks": ["Yi Syllables"],
        "optional_blocks": [],
    },
    # Japanese
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
    # Georgian
    "ka": {
        "scripts": ["Georgian"],
        "required_blocks": ["Georgian"],
        "optional_blocks": ["Georgian Supplement"],
    },
    # Lao
    "lo": {
        "scripts": ["Lao"],
        "required_blocks": ["Lao"],
        "optional_blocks": [],
    },
    # Myanmar
    "my": {
        "scripts": ["Myanmar"],
        "required_blocks": ["Myanmar", "Myanmar Extended-A", "Myanmar Extended-B"],
        "optional_blocks": [],
    },
    # Russian
    "ru": {
        "scripts": ["Cyrillic"],
        "required_blocks": ["Cyrillic"],
        "optional_blocks": ["Cyrillic Supplement"],
    },
    # Tamil
    "ta": {
        "scripts": ["Tamil"],
        "required_blocks": ["Tamil", "Tamil Supplement"],
        "optional_blocks": [],
    },
    # Thai
    "th": {
        "scripts": ["Thai"],
        "required_blocks": ["Thai"],
        "optional_blocks": [],
    },
    # Chinese
    "zh": {
        "scripts": ["Han"],
        "required_blocks": ["CJK Unified Ideographs"],
        "optional_blocks": [],
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
    "arab": "ar",
    "armn": "hy",
    "beng": "bn",
    "bugi": "bug",
    "buhd": "bku",
    "cher": "chr",
    "cyrl": "ru",
    "deva": "hi",
    "ethi": "ti",
    "geor": "ka",
    "grek": "el",
    "hang": "ko",
    "hani": "zh",
    "hebr": "he",
    "jpan": "ja",
    "khmr": "km",
    "laoo": "lo",
    "latn": "en",
    "mymr": "my",
    "taml": "ta",
    "thai": "th",
    "yiii": "ii",
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

    # ------------------------------------------------------------------
    # Script Gate (Step 1 — charset-derived inference only)
    #
    # Languages are considered only if their primary script belongs
    # to the inferred script set.
    #
    # Disabled when no scripts are inferred (emoji/symbol fonts).
    # ------------------------------------------------------------------

    scripts_public = coverage.get("scripts")
    inferred_scripts = (
        [str(s).lower() for s in scripts_public]
        if isinstance(scripts_public, list)
        else None
    )

    allowed_languages: set[str] | None = None

    if inferred_scripts:
        scripts_upper = {s.upper() for s in inferred_scripts}

        allowed_languages = {
            lang
            for lang, script in LANGUAGE_PRIMARY_SCRIPT.items()
            if script in scripts_upper
        }

    for lang, profile in LANGUAGE_PROFILES.items():
        if allowed_languages is not None and lang not in allowed_languages:
            continue

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

    # ------------------------------------------------------------------
    # Script-authoritative fallback rules
    # ------------------------------------------------------------------

    scripts: list[str] | None = None

    # Canonical script source (Step 3.1)
    scripts_public = coverage.get("scripts")
    if isinstance(scripts_public, list) and scripts_public:
        scripts = [str(s).lower() for s in scripts_public]

    if inferred:
        # Canonical Latin fallback:
        # if LATN is the only inferred script, collapse to English.
        if isinstance(scripts, list) and set(scripts) == {"latn"} and "en" in inferred:
            unicode_blocks = coverage.get("unicode_blocks", {}) or {}
            blocks_present = set(unicode_blocks.keys())

            # Minimal Latin capability → canonical English fallback
            if blocks_present == {"Basic Latin"}:
                inferred = {"en": inferred["en"]}

    elif isinstance(scripts, list) and scripts:  # Script-driven display fallback
        # Deterministic primary script selection
        primary = sorted(str(s).lower() for s in scripts)[0]
        lang = SCRIPT_TO_DISPLAY_LANGUAGE.get(primary) or ""
        if lang:
            inferred[lang] = LanguageInferenceInfo(
                confidence="medium",
                evidence=["script-default"],
            )

    # Deterministic ordering safeguard:
    # rebuild dictionary ordered by language code.
    return dict(sorted(inferred.items(), key=lambda kv: kv[0]))
