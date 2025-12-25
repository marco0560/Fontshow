#!/usr/bin/env python3
"""
Fontshow – parse_font_inventory.py
=================================

Parse and enrich a ``font_inventory.json`` produced by ``dump_fonts.py`` by
applying deterministic inference of writing scripts and language candidates.

Design principles
-----------------
- **Cross-platform**: works only on JSON data, never touches font files.
- **Deterministic**: same input → same output.
- **Non-destructive**: declared metadata is never overwritten.
- **Configurable**: inference aggressiveness selectable from CLI.

Default inference level: ``medium``.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# ============================================================
# Inference thresholds
# ============================================================

#: Mapping of inference level → numeric thresholds.
#:
#: Structure::
#:
#:     {
#:         "<level>": {
#:             "script_min_cp": int,  # minimum code points to consider a script
#:         }
#:     }
#:
INFERENCE_THRESHOLDS: dict[str, dict[str, int]] = {
    "conservative": {
        "script_min_cp": 10,
    },
    "medium": {
        "script_min_cp": 5,
    },
    "aggressive": {
        "script_min_cp": 1,
    },
}

# ============================================================
# Unicode → script ranges
# ============================================================

#: Mapping of ISO 15924 script codes to Unicode code point ranges.
#:
#: Each value is a list of ``(start, end)`` integer tuples, inclusive.
#:
#: Example::
#:
#:     "latn": [(0x0041, 0x007A), (0x00C0, 0x024F)]
#:
UNICODE_SCRIPT_RANGES: dict[str, list[tuple[int, int]]] = {
    "latn": [(0x0041, 0x007A), (0x00C0, 0x024F)],
    "grek": [(0x0370, 0x03FF), (0x1F00, 0x1FFF)],
    "cyrl": [(0x0400, 0x04FF), (0x0500, 0x052F)],
    "arab": [(0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF)],
    "hebr": [(0x0590, 0x05FF)],
    "deva": [(0x0900, 0x097F)],
    "hani": [(0x4E00, 0x9FFF)],
    "hang": [(0xAC00, 0xD7AF)],
    "thai": [(0x0E00, 0x0E7F)],
    # Requested additions
    "armn": [(0x0530, 0x058F)],  # Armenian
    "jpan": [(0x3040, 0x30FF)],  # Japanese (Hiragana + Katakana)
    "viet": [(0x1EA0, 0x1EFF)],  # Vietnamese extensions
    "copt": [(0x2C80, 0x2CFF)],  # Coptic
    "ethi": [(0x1200, 0x137F)],  # Ethiopic (incl. Tigrinya)
}

# ============================================================
# Script → language candidates
# ============================================================

#: Mapping of inferred script identifiers to plausible language codes.
#:
#: Values are **examples**, not a guarantee of full language support.
#:
SCRIPT_TO_LANGUAGES: dict[str, list[str]] = {
    "latn": ["en", "it", "fr", "de", "es", "vi"],
    "grek": ["el"],
    "cyrl": ["ru", "uk", "bg"],
    "arab": ["ar"],
    "hebr": ["he"],
    "deva": ["hi"],
    "hani": ["zh"],
    "hang": ["ko"],
    "thai": ["th"],
    "armn": ["hy"],
    "jpan": ["ja"],
    "viet": ["vi"],
    "copt": ["cop"],
    "ethi": ["ti"],
}


# ============================================================
# Helper functions
# ============================================================


def validate_inventory(data: dict) -> int:
    errors = 0

    if not isinstance(data, dict):
        print("❌ Inventory root is not a JSON object")
        return 1

    metadata = data.get("metadata", {})
    schema_version = metadata.get("schema_version")

    if schema_version is None:
        print("⚠️  Warning: missing schema_version")
    elif schema_version != "1.0":
        print(f"⚠️  Warning: unknown schema_version '{schema_version}'")

    fonts = data.get("fonts")
    if not isinstance(fonts, list):
        print("❌ 'fonts' field missing or not a list")
        return 1

    for idx, font in enumerate(fonts):
        if not isinstance(font, dict):
            print(f"❌ Font entry #{idx} is not an object")
            errors += 1
            continue

        identity = font.get("identity", {})
        family = identity.get("family")
        base_names = font.get("base_names")

        if not family and not base_names:
            errors += 1
            font_path = (
                font.get("path")
                or font.get("file")
                or font.get("source", {}).get("path")
                or "<unknown path>"
            )
            print(
                f"⚠️  Warning: font entry #{idx} ({font_path}) has no family or base_names"
            )

    if errors == 0:
        print("✅ Inventory validation completed (no fatal errors)")
    else:
        print(f"❌ Inventory validation failed with {errors} errors")

    return errors


# ============================================================
# Inference helpers
# ============================================================


def infer_scripts(coverage: dict[str, Any], level: str = "medium") -> list[str]:
    """
    Infer writing scripts from Unicode coverage metadata.

    The function follows a two-step strategy:

    1. **Primary path**: analyze ``coverage["unicode_blocks"]`` if present.
    2. **Fallback path**: infer from ``coverage["unicode"]["max"]``.

    Args:
        coverage: Coverage block extracted from a font entry. Expected keys are
            ``unicode_blocks`` (mapping block name → count) and/or
            ``unicode.max`` (maximum code point).
        level: Inference aggressiveness level. One of
            ``"conservative"``, ``"medium"`` (default), or ``"aggressive"``.

    Returns:
        A list of inferred script identifiers (lowercase strings).
        Returns ``["unknown"]`` if no reliable inference is possible.
    """
    blocks: dict[str, int] = coverage.get("unicode_blocks", {}) or {}

    # -------------------------------
    # 1. Primary path: unicode_blocks
    # -------------------------------
    if blocks:
        total = sum(blocks.values()) or 1

        def significant(count: int) -> bool:
            """Check whether a block count is significant for the given level."""
            if level == "conservative":
                return count >= 50 or (count / total) >= 0.10
            if level == "aggressive":
                return count >= 5
            # medium (default)
            return count >= 20 or (count / total) >= 0.05

        scripts_found: set[str] = set()

        # --- block → script mapping
        for block, count in blocks.items():
            if not significant(count):
                continue

            if block.startswith("Latin"):
                scripts_found.add("latin")
            elif block == "Greek and Coptic":
                scripts_found.add("greek")
            elif block == "Cyrillic":
                scripts_found.add("cyrillic")
            elif block == "Arabic":
                scripts_found.add("arabic")
            elif block == "Hebrew":
                scripts_found.add("hebrew")
            elif block == "Devanagari":
                scripts_found.add("devanagari")
            elif block in ("Hiragana", "Katakana"):
                scripts_found.add("japanese")
            elif block == "Hangul Syllables":
                scripts_found.add("korean")
            elif block.startswith("CJK Unified Ideographs"):
                scripts_found.add("han")

        # --- CJK disambiguation
        if "han" in scripts_found:
            if "japanese" in scripts_found:
                return ["japanese"]
            if "korean" in scripts_found:
                return ["korean"]
            return ["han"]

        return sorted(scripts_found) or ["unknown"]

    # -------------------------------
    # 2. Fallback: unicode.max
    # -------------------------------
    unicode_max = coverage.get("unicode", {}).get("max")
    if isinstance(unicode_max, int):
        if unicode_max <= 0x024F:
            return ["latin"]
        if 0x0370 <= unicode_max <= 0x03FF:
            return ["greek"]
        if 0x0400 <= unicode_max <= 0x04FF:
            return ["cyrillic"]
        if 0x0590 <= unicode_max <= 0x05FF:
            return ["hebrew"]
        if 0x0600 <= unicode_max <= 0x06FF:
            return ["arabic"]
        if 0x0900 <= unicode_max <= 0x097F:
            return ["devanagari"]
        if unicode_max >= 0x4E00:
            return ["han"]

    return ["unknown"]


def infer_languages(scripts: list[str]) -> list[str]:
    """
    Infer plausible language codes from inferred scripts.

    Args:
        scripts: List of script identifiers as returned by :func:`infer_scripts`.

    Returns:
        A sorted list of unique language codes.
    """
    langs: list[str] = []
    for script in scripts:
        langs.extend(SCRIPT_TO_LANGUAGES.get(script, []))
    return sorted(set(langs))


# ============================================================
# Core processing
# ============================================================


def parse_inventory(data: dict[str, Any], level: str) -> dict[str, Any]:
    """
    Enrich a font inventory with deterministic inference results.

    The function iterates over ``data["fonts"]`` and adds an ``inference``
    block to each font entry.

    Added structure::

        font["inference"] = {
            "level": str,
            "scripts": list[str],
            "languages": list[str],
            "declared_scripts": list[str],
            "declared_languages": list[str],
            "unicode_blocks": dict[str, int],
        }

    Args:
        data: Parsed JSON inventory as a Python dictionary.
        level: Inference aggressiveness level.

    Returns:
        The same inventory dictionary, enriched in place.
    """
    for font in data.get("fonts", []):
        coverage: dict[str, Any] = font.get("coverage", {}) or {}

        declared_scripts: list[str] = coverage.get("scripts", [])
        declared_languages: list[str] = coverage.get("languages", [])

        inferred_scripts: list[str] = list(infer_scripts(coverage, level) or [])
        inferred_languages: list[str] = list(infer_languages(inferred_scripts) or [])

        font["inference"] = {
            "level": level,
            "scripts": inferred_scripts,
            "languages": inferred_languages,
            "declared_scripts": declared_scripts,
            "declared_languages": declared_languages,
            "unicode_blocks": coverage.get("unicode_blocks", {}),
        }

    metadata = data.setdefault("metadata", {})
    metadata["inference_level"] = level
    metadata.setdefault("schema_version", "1.0")

    return data


# ============================================================
# CLI
# ============================================================


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Parse and enrich a Fontshow font_inventory.json with deterministic inference.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        default=Path("font_inventory.json"),
        help="Input font_inventory.json generated by dump_fonts.py",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("font_inventory_enriched.json"),
        help="Output enriched JSON file",
    )
    parser.add_argument(
        "--infer-level",
        choices=["conservative", "medium", "aggressive"],
        default="medium",
        help="Inference aggressiveness level",
    )
    parser.add_argument(
        "--validate-inventory",
        action="store_true",
        help="Validate inventory structure and exit (no output generation)",
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"❌ Error: input file not found: {args.input}", file=sys.stderr)
        print(
            "Hint: run dump_fonts.py first to generate the inventory.", file=sys.stderr
        )
        sys.exit(1)

    data: dict[str, Any] = json.loads(args.input.read_text(encoding="utf-8"))

    # --- Soft schema validation ---
    metadata = data.setdefault("metadata", {})

    schema_version = metadata.get("schema_version")
    if schema_version is None:
        print("⚠️  Warning: inventory has no 'schema_version'; assuming legacy format")
        metadata["schema_version"] = "1.0"
    elif schema_version != "1.0":
        print(
            f"⚠️  Warning: unsupported schema_version '{schema_version}', attempting best-effort parsing"
        )

    fonts = data.get("fonts")
    if not isinstance(fonts, list):
        raise TypeError("Invalid inventory JSON: 'fonts' must be a list")

    # ------------------------------
    if args.validate_inventory:
        exit_code = validate_inventory(data)
        sys.exit(exit_code)

    enriched = parse_inventory(data, args.infer_level)

    args.output.write_text(
        json.dumps(enriched, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"OK: wrote enriched inventory to {args.output}")


if __name__ == "__main__":
    main()
