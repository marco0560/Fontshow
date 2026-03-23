"""
Semantic validation helpers for inventory data.

This module performs semantic consistency checks on enriched Fontshow
inventory structures.

Responsibilities
----------------
- Validate semantic correctness of normalized inventory metadata.
- Detect invalid or deprecated language codes.
- Emit structured warnings describing semantic issues.

Design principles
-----------------
Semantic validation must not modify inventory data. It operates only as
a diagnostic stage that reports issues through structured warnings.

Architectural role
------------------
This module belongs to the **inventory subsystem** and performs semantic
validation after metadata enrichment and before downstream catalog
processing.
"""

from __future__ import annotations

import re
from typing import Any

import pycountry

from fontshow.core.logging_utils import log, log_trace_cat
from fontshow.core.types import (
    DeprecatedLanguageInfo,
    DroppedLanguageInfo,
    NormalizeLanguagesResult,
    Severity,
)

# NOTE:
# pycountry is not a full mirror of the IANA language subtag registry.
# Some valid BCP-47 primary language subtags may be missing in pycountry.
#
# We keep a *minimal* explicit allowlist for codes we know we want to accept
# in Fontshow inventories (example: user reported 'yuw' as valid BCP-47).
_EXTRA_LANGUAGE_ALLOWLIST: set[str] = {
    "ber",  # Berber languages (ISO 639-2 collective); may appear after stripping region.
    "kab",  # Kabyle (ISO 639-3); user reported.
    "rif",  # Tarifit (ISO 639-3); user reported.
    "wen",  # Sorbian languages (ISO 639-2 collective); may appear as "wen".
    "yuw",  # Yau (ISO 639-3) — user validated against IANA BCP-47 registry.
}

# Minimal deprecated-language mapping.
# This is intentionally small and explicit to avoid guessing large tables.
_DEPRECATED_LANGUAGE_MAP: dict[str, str] = {
    "in": "id",
    "iw": "he",
    "ji": "yi",
    "mo": "ro",
    "sh": "sr",
}

# Heuristic BCP-47-ish structural check (not full ABNF):
# - allow letters/digits separated by '-' or '_'
# - allow optional trailing parenthesized suffix (e.g. yuw(s))
# - we only use this when strict_bcp47=True
_BCP47_HEURISTIC_RE = re.compile(r"^[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*(\(.*\))?$")


def _is_known_language(code: str) -> bool:
    """
    Check whether a primary language subtag is "known enough" for Fontshow.

    Parameters
    ----------
    code : str
        Primary language subtag to validate.

    Returns
    -------
    bool
        True if the code is accepted by the explicit allowlist or by
        `pycountry` ISO-639 lookup.

    Notes
    -----
    Order:
    1. Explicit allowlist (covers gaps in pycountry).
    2. pycountry ISO-639-1/3 lookup.
    """
    if code in _EXTRA_LANGUAGE_ALLOWLIST:
        return True

    return bool(
        pycountry.languages.get(alpha_2=code) or pycountry.languages.get(alpha_3=code)
    )


def normalize_languages(
    raw_languages: list[str],
    *,
    strict_bcp47: bool = False,
) -> NormalizeLanguagesResult:
    """
    Normalize raw language tags into ISO-compatible primary language codes.

    Parameters
    ----------
    raw_languages : list[str]
        Raw language tags to normalize.
    strict_bcp47 : bool, optional
        If True, reject tags that fail the heuristic BCP-47 structural
        check before normalization.

    Returns
    -------
    NormalizeLanguagesResult
        Structured result containing normalized codes, deprecated-code
        remaps, and dropped inputs with reasons.

    Notes
    -----
    Pipeline (non-strict):
    - strip whitespace
    - lowercase
    - strip parentheses suffix   (yuw(s) -> yuw)
    - strip region/script/variants (az-az -> az, pt_BR -> pt)
    - map known deprecated codes  (mo -> ro)
    - validate as ISO-639-1/3 (with a small allowlist)
    - deduplicate (preserving order)

    Pipeline (strict_bcp47=True):
    - before any normalization, ensure raw matches a BCP-47-ish
      structural regex (heuristic; not full ABNF). If it fails, drop as
      invalid_bcp47.

    Returned structure:
        {
            "normalized": [str],
            "deprecated": [{"raw": str, "from": str, "to": str}],
            "dropped": [{"raw": str, "reason": str, ...}]
        }

    Drop reasons:
    - invalid_format
    - invalid_bcp47
    - unknown_language
    - duplicate_normalized
    - variant_stripped
    """

    normalized: list[str] = []
    deprecated: list[DeprecatedLanguageInfo] = []
    dropped: list[DroppedLanguageInfo] = []
    seen: set[str] = set()

    for raw in raw_languages:
        original = raw

        if not isinstance(raw, str) or not raw.strip():
            dropped.append({"raw": original, "reason": "invalid_format"})
            continue

        value = raw.strip()

        if strict_bcp47 and not _BCP47_HEURISTIC_RE.match(value):
            dropped.append({"raw": original, "reason": "invalid_bcp47"})
            continue

        # Normalize case early so that case-only differences don't become "variant_stripped".
        value = value.lower()

        # Strip trailing parentheses suffixes: bem(s) -> bem
        value = re.sub(r"\(.*\)$", "", value)

        # Strip region/script/variants by taking the first component.
        base = re.split(r"[-_]", value)[0]

        # Map deprecated codes if known.
        mapped = _DEPRECATED_LANGUAGE_MAP.get(base, base)
        if mapped != base:
            deprecated.append({"raw": original, "from_": base, "to": mapped})

        # Validate.
        if not _is_known_language(mapped):
            dropped.append({"raw": original, "reason": "unknown_language"})
            continue

        # Deduplicate (duplicate after normalization)
        if mapped in seen:
            dropped.append(
                {
                    "raw": original,
                    "reason": "duplicate_normalized",
                    "normalized": mapped,
                }
            )
            continue

        # Variant stripped (only when it is the first occurrence).
        # This ensures inputs like ar_IN, ar_IQ, ar_JO become:
        # - first: variant_stripped
        # - subsequent: duplicate
        #
        # NOTE: deprecated remaps are reported via the "deprecated" bucket instead.
        if mapped == base and mapped != original.strip().lower():
            dropped.append({"raw": original, "reason": "variant_stripped"})

        normalized.append(mapped)
        seen.add(mapped)

    return NormalizeLanguagesResult(
        normalized=normalized,
        deprecated=deprecated,
        dropped=dropped,
    )


def validate_language_codes(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Check semantic consistency of an enriched Fontshow inventory.

    Parameters
    ----------
    inventory : dict[str, Any]
        Enriched inventory structure to inspect.

    Returns
    -------
    list[dict[str, Any]]
        Structured warning records describing invalid or suspicious
        language codes.

    Notes
    -----
    The function inspects both coverage languages and inferred
    languages, skipping the sentinel value ``"unknown"``.
    This function performs semantic checks without modifying data.
    All detected issues are reported as structured warnings.
    No inference, normalization, or enrichment is performed here.
    """
    warnings: list[dict[str, Any]] = []

    log_trace_cat(
        log,
        "validate",
        "semantic validation started",
        extra={},
    )

    raw_fonts = inventory.get("fonts")
    fonts = raw_fonts if isinstance(raw_fonts, list) else []

    for idx, font in enumerate(fonts):
        if not isinstance(font, dict):
            continue

        font_name = font.get("name") or font.get("id") or f"font[{idx}]"

        codes: set[str] = set()

        coverage = font.get("coverage")
        if isinstance(coverage, dict):
            codes.update(coverage.get("languages", []) or [])

        inference = font.get("inference")
        if isinstance(inference, dict):
            codes.update(inference.get("languages", []) or [])

        for code in sorted(codes):
            if code == "unknown":
                continue

            if not _is_known_language(code):
                log_trace_cat(
                    log,
                    "validate",
                    "semantic rule triggered",
                    extra={
                        "severity": Severity.WARN,
                        "code": "invalid_language_code",
                        "font": font_name,
                        "language": code,
                        "rule": code,
                        "message": f"Invalid language code: '{code}'",
                    },
                )
                warnings.append(
                    {
                        "severity": Severity.WARN,
                        "code": "invalid_language_code",
                        "font": font_name,
                        "language": code,
                        "message": f"Invalid language code: '{code}'",
                    }
                )

    return warnings


def enforce_semantic_validation(
    inventory: dict, strict: bool
) -> tuple[bool, list[dict]]:
    """
    Perform semantic validation.

    Parameters
    ----------
    inventory : dict
        Inventory structure to validate semantically.
    strict : bool
        Whether warnings with warning-or-error severity should cause the
        overall validation result to fail.

    Returns
    -------
    tuple[bool, list[dict]]
        Pair ``(ok, warnings)`` where ``ok`` indicates whether semantic
        validation passed and ``warnings`` contains the accumulated
        structured warning records.

    Notes
    -----
    - ``ok == True`` means semantic validation passed.
    - ``ok == False`` means semantic validation failed, which is only
      possible in strict mode.
    """
    warnings = []

    # Language-level semantic warnings
    warnings.extend(validate_language_codes(inventory))

    # Inventory-level semantic warnings
    inv_warnings = inventory.get("warnings", [])
    if isinstance(inv_warnings, list):
        warnings.extend(inv_warnings)

    if not strict:
        return True, warnings

    for w in warnings:
        sev = w.get("severity")
        if sev in (Severity.WARN, Severity.ERROR):
            log_trace_cat(
                log,
                "validate",
                "semantic validation failed",
                extra={
                    "rule": "strict_semantic_validation",
                    "severity": sev,
                    "strict": True,
                    "warnings_count": len(warnings),
                },
            )
            return False, warnings

    log_trace_cat(
        log,
        "validate",
        "semantic validation completed",
        extra={
            "warnings_count": len(warnings),
        },
    )

    return True, warnings
