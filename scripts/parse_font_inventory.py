#!/usr/bin/env python3
"""
Fontshow – parse_font_inventory.py
=================================

Parse and enrich a font_inventory.json produced by dump_fonts.py by applying
deterministic inference of scripts and languages.

Design principles
-----------------
- Cross-platform: works only on JSON, never touches font files.
- Deterministic: same input → same output.
- Non-destructive: declared metadata is never overwritten.
- Configurable: inference aggressiveness selectable from CLI.

Default inference level: MEDIUM
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

# ============================================================
# Inference thresholds
# ============================================================

INFERENCE_THRESHOLDS = {
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

UNICODE_SCRIPT_RANGES: Dict[str, List[Tuple[int, int]]] = {
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

SCRIPT_TO_LANGUAGES = {
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
# Inference helpers
# ============================================================


def infer_scripts(unicode_max: str | None, level: str) -> List[str]:
    """
    Infer supported scripts from Unicode coverage.

    Strategy:
    - use the maximum Unicode codepoint covered by the font
    - match against known Unicode ranges
    - require a minimum threshold depending on inference level
    """
    if not unicode_max or not unicode_max.startswith("U+"):
        return []

    max_cp = int(unicode_max[2:], 16)
    threshold = INFERENCE_THRESHOLDS[level]["script_min_cp"]

    scripts: List[str] = []
    for script, ranges in UNICODE_SCRIPT_RANGES.items():
        count = 0
        for start, end in ranges:
            if start <= max_cp <= end:
                count += 1
        if count >= threshold:
            scripts.append(script)

    return sorted(set(scripts))


def infer_languages(scripts: List[str]) -> List[str]:
    """
    Infer language candidates from inferred scripts.

    Languages are *plausible examples*, not a certification of support.
    """
    langs: List[str] = []
    for script in scripts:
        langs.extend(SCRIPT_TO_LANGUAGES.get(script, []))
    return sorted(set(langs))


# ============================================================
# Core processing
# ============================================================


def parse_inventory(data: dict, level: str) -> dict:
    """
    Enrich the inventory with inference results.

    Adds an `inference` block to each font.
    """
    for font in data.get("fonts", []):
        coverage = font.get("coverage", {})
        unicode_max = coverage.get("unicode", {}).get("max")

        declared_scripts = coverage.get("scripts", [])
        declared_languages = coverage.get("languages", [])

        inferred_scripts = infer_scripts(unicode_max, level)
        inferred_languages = infer_languages(inferred_scripts)

        font["inference"] = {
            "level": level,
            "scripts": inferred_scripts,
            "languages": inferred_languages,
            "declared_scripts": declared_scripts,
            "declared_languages": declared_languages,
        }

    data.setdefault("metadata", {})["inference_level"] = level
    return data


# ============================================================
# CLI
# ============================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse and enrich a Fontshow font_inventory.json with deterministic inference.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input",
        type=Path,
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

    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    enriched = parse_inventory(data, args.infer_level)

    args.output.write_text(
        json.dumps(enriched, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"OK: wrote enriched inventory to {args.output}")


if __name__ == "__main__":
    main()
