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


def infer_scripts(
    coverage: dict,
    level: str = "medium",
) -> list[str]:
    """
    Infer supported scripts from coverage information.

    Strategy:
    - Prefer coverage.charset when available (Linux / FontConfig).
    - Fallback to coverage.unicode.count when charset is missing.

    Parameters
    ----------
    coverage : dict
        coverage block from inventory:
        {
          "unicode": {"count": int, "min": int|None, "max": int|None},
          "charset": str|None
        }
    level : str
        "conservative" | "medium" | "aggressive"

    Returns
    -------
    list[str]
        List of inferred script tags (e.g. ["latin", "greek"])
    """

    level = level.lower()
    assert level in {"conservative", "medium", "aggressive"}

    charset_blob = coverage.get("charset")
    unicode_count = coverage.get("unicode", {}).get("count", 0)

    inferred: list[str] = []

    # -------------------------
    # Case 1: charset available
    # -------------------------
    if charset_blob:
        # Parse charset ranges: e.g. "U+0000-00FF U+0400-04FF ..."
        ranges: list[tuple[int, int]] = []

        for token in charset_blob.replace(",", " ").split():
            if token.startswith("U+"):
                part = token[2:]
                if "-" in part:
                    a, b = part.split("-", 1)
                    try:
                        ranges.append((int(a, 16), int(b, 16)))
                    except ValueError:
                        continue
                else:
                    try:
                        cp = int(part, 16)
                        ranges.append((cp, cp))
                    except ValueError:
                        continue

        # Thresholds per level (absolute codepoints)
        min_hits = {
            "conservative": 30,
            "medium": 10,
            "aggressive": 1,
        }[level]

        for script, script_ranges in UNICODE_SCRIPT_RANGES.items():
            hits = 0
            for r_start, r_end in ranges:
                for s_start, s_end in script_ranges:
                    # overlap length
                    lo = max(r_start, s_start)
                    hi = min(r_end, s_end)
                    if lo <= hi:
                        hits += hi - lo + 1
                        if hits >= min_hits:
                            inferred.append(script)
                            break
                if script in inferred:
                    break

        return sorted(inferred)

    # --------------------------------
    # Case 2: fallback on unicode.count
    # --------------------------------
    if not isinstance(unicode_count, int) or unicode_count <= 0:
        return []

    # Very rough heuristics
    if level == "aggressive":
        # allow all scripts whose primary range could plausibly fit
        return ["latin"] if unicode_count < 300 else ["latin", "symbol"]

    if level == "medium":
        if unicode_count < 2000:
            return ["latin"]
        if unicode_count < 5000:
            return ["latin", "greek", "cyrillic"]
        return []

    # conservative
    if unicode_count < 1000:
        return ["latin"]

    return []


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

        inferred_scripts = infer_scripts(coverage, level)
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
