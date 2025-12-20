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


def infer_scripts(coverage: dict, level: str = "medium") -> list[str]:
    """
    Infer writing scripts from Unicode coverage.

    Primary source: coverage["unicode_blocks"]
    Fallback: coverage["unicode"]["max"]
    """
    blocks: dict[str, int] = coverage.get("unicode_blocks", {}) or {}

    # -------------------------------
    # 1. Primary path: unicode_blocks
    # -------------------------------
    if blocks:
        total = sum(blocks.values()) or 1

        def significant(count: int) -> bool:
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
    Infer language candidates from inferred scripts.

    Languages are *plausible examples*, not a certification of support.
    """
    langs: list[str] = []
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
        coverage = font.get("coverage", {}) or {}

        declared_scripts = coverage.get("scripts", [])
        declared_languages = coverage.get("languages", [])

        inferred_scripts = list(infer_scripts(coverage, level) or [])
        inferred_languages = list(infer_languages(inferred_scripts) or [])

        font["inference"] = {
            "level": level,
            "scripts": inferred_scripts,
            "languages": inferred_languages,
            "declared_scripts": declared_scripts,
            "declared_languages": declared_languages,
            "unicode_blocks": coverage.get("unicode_blocks", {}),
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
