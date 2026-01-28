"""
Semantic validation for enriched Fontshow inventories.

This module performs semantic consistency checks on enriched inventory data.

Semantic validation:
- does NOT perform inference
- does NOT modify inventory content
- reports issues via structured warnings only
- distinguishes normalization from actual errors
"""

from typing import Any

import language_tags
import pycountry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_valid_bcp47(tag: str) -> bool:
    """Return True if tag is syntactically valid BCP-47."""
    try:
        language_tags.tags.check(tag)
        return True
    except Exception:
        return False


def _is_known_language(tag: str) -> bool:
    """Return True if tag matches an ISO 639 language."""
    return (
        pycountry.languages.get(alpha_2=tag) is not None
        or pycountry.languages.get(alpha_3=tag) is not None
    )


# ---------------------------------------------------------------------------
# Language normalization
# ---------------------------------------------------------------------------


def normalize_languages(raw_languages: list[str]) -> dict[str, list[dict]]:
    """
    Normalize raw language tags.

    Pipeline:
    1. Trim and lowercase
    2. Strip parentheses
    3. Strip region / script
    4. Validate ISO-639
    5. Deduplicate

    Returns:
        {
            "normalized": [str],
            "dropped": [
                {"raw": str, "reason": str}
            ]
        }
    """

    normalized: list[str] = []
    dropped: list[dict] = []
    seen: set[str] = set()

    for raw in raw_languages:
        original = raw

        if not isinstance(raw, str) or not raw.strip():
            dropped.append({"raw": original, "reason": "invalid_format"})
            continue

        value = raw.strip().lower()

        reason = None

        # Strip parentheses
        if "(" in value:
            value = value.split("(", 1)[0]
            reason = "variant_stripped"

        # Strip region/script
        if "-" in value:
            value = value.split("-", 1)[0]
            reason = "variant_stripped"
        elif "_" in value:
            value = value.split("_", 1)[0]
            reason = "variant_stripped"

        # ISO validation
        if not _is_known_language(value):
            dropped.append({"raw": original, "reason": "unknown_language"})
            continue

        # Deduplication
        if value in seen:
            dropped.append(
                {
                    "raw": original,
                    "reason": "duplicate_normalized",
                    "normalized": value,
                }
            )

            continue

        # If we normalized but kept the value
        if reason:
            dropped.append({"raw": original, "reason": reason})

        normalized.append(value)
        seen.add(value)

    return {
        "normalized": normalized,
        "dropped": dropped,
    }


# ---------------------------------------------------------------------------
# Semantic validation
# ---------------------------------------------------------------------------


def validate_language_codes(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Validate normalized language codes in an enriched inventory.

    Rules:
    - Only normalized language lists are checked
    - Raw language tags are ignored
    - 'unknown' is ignored
    - Only invalid ISO-639 codes emit warnings
    """

    warnings: list[dict[str, Any]] = []

    for idx, font in enumerate(inventory.get("fonts", [])):
        font_id = font.get("path") or f"font[{idx}]"

        codes = set()
        codes.update(font.get("coverage", {}).get("languages", []) or [])
        codes.update(font.get("inference", {}).get("languages", []) or [])

        for code in sorted(codes):
            if code == "unknown":
                continue

            if not _is_known_language(code):
                warnings.append(
                    {
                        "severity": "warning",
                        "code": "invalid_language_code",
                        "font": font_id,
                        "language": code,
                        "message": f"Invalid or deprecated language code: '{code}'",
                    }
                )

    return warnings
