from typing import Any

import pycountry


def validate_language_codes(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Validate ISO language codes found in a Fontshow inventory.

    This function performs semantic validation beyond JSON Schema,
    checking that all inferred and declared language codes correspond
    to valid ISO 639 identifiers.

    Returns structured warnings; never raises.
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
