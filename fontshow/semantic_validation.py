"""
Semantic validation for enriched Fontshow inventories.

This module performs semantic consistency checks on enriched inventory data.
Semantic validation:
- does not perform inference,
- does not normalize or modify data,
- reports issues exclusively via structured warnings.

Semantic validation is distinct from both schema validation and inference logic.
"""

import re
from typing import Any

import pycountry


def normalize_languages(raw_languages: list[str]) -> dict[str, list[dict[str, Any]]]:
    """
    Normalize raw language tags into ISO-compatible language codes.

    Returns a dict with:
        - "normalized": list[str]
        - "dropped": list[{"raw": str, "reason": str}]

    Rules:
    - split on '-' or '_'
    - remove trailing parentheses
    - lowercase
    - validate against ISO 639
    - deduplicate while preserving order
    """

    normalized: list[str] = []
    dropped: list[dict[str, Any]] = []

    seen: set[str] = set()

    for raw in raw_languages:
        original = raw

        # Basic sanity check
        if not isinstance(raw, str) or not raw.strip():
            dropped.append(
                {
                    "raw": original,
                    "reason": "invalid_format",
                }
            )
            continue

        # Remove parenthesized suffixes: bem(s) → bem
        value = re.sub(r"\(.*\)$", "", raw)

        # Split on '-' or '_'
        value = re.split(r"[-_]", value)[0]

        # Normalize case
        value = value.lower()

        # ISO 639 validation
        if not pycountry.languages.get(alpha_2=value) and not pycountry.languages.get(
            alpha_3=value
        ):
            dropped.append(
                {
                    "raw": original,
                    "reason": "unknown_language",
                }
            )
            continue

        # Deduplication
        if value in seen:
            dropped.append(
                {
                    "raw": original,
                    "reason": "duplicate",
                }
            )
            continue

        # Variant stripped
        if value != original.lower():
            dropped.append(
                {
                    "raw": original,
                    "reason": "variant_stripped",
                }
            )

        normalized.append(value)
        seen.add(value)

    return {
        "normalized": normalized,
        "dropped": dropped,
    }


def validate_language_codes(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Check semantic consistency of an enriched Fontshow inventory.

    This function performs semantic checks without modifying data.
    All detected issues are reported as structured warnings.

    No inference, normalization, or enrichment is performed here.
    """
    warnings: list[dict[str, Any]] = []

    fonts = inventory.get("fonts", [])

    for idx, font in enumerate(fonts):
        font_name = font.get("name") or font.get("id") or f"font[{idx}]"

        codes: set[str] = set()

        # Declared languages
        codes.update(font.get("coverage", {}).get("languages", []) or [])

        # Inferred languages
        codes.update(font.get("inference", {}).get("languages", []) or [])

        for code in sorted(codes):
            if code == "unknown":
                continue

            lang = pycountry.languages.get(alpha_2=code) or pycountry.languages.get(
                alpha_3=code
            )

            # Only validate normalized language codes.
            # Raw language tags are stored in coverage["languages_raw"]
            # and must not be validated here.
            if not lang:
                warnings.append(
                    {
                        "severity": "warning",
                        "code": "invalid_language_code",
                        "font": font_name,
                        "language": code,
                        "message": f"Invalid ISO 639 language code: '{code}'",
                    }
                )

    return warnings
