"""
Semantic validation for enriched Fontshow inventories.

This module performs semantic consistency checks on enriched inventory data.
Semantic validation:
- does not perform inference,
- does not normalize or modify data,
- reports issues exclusively via structured warnings.

Semantic validation is distinct from both schema validation and inference logic.
"""

from typing import Any

import pycountry


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
