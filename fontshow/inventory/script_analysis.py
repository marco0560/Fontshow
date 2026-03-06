"""
Script coverage analysis utilities for inventory processing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fontshow.unicode_tables import UNICODE_BLOCK_RANGES

if TYPE_CHECKING:
    from fontshow.types import ScriptISO


def script_coverage_from_unicode_blocks(
    unicode_blocks: dict[str, int],
    script_ranges: dict[ScriptISO, list[tuple[int, int]]],
    total_codepoints: int,
) -> dict[str, float]:
    """
    Derive script coverage ratios from Unicode block coverage.

    Parameters
    ----------
    unicode_blocks : dict[str, int]
        Mapping of Unicode block name to covered codepoint count.
    script_ranges : dict[str, list[tuple[int, int]]]
        Mapping of script tag to Unicode codepoint ranges.
    total_codepoints : int
        Total number of codepoints covered by the charset.

    Returns
    -------
    dict[str, float]
        Mapping of script tag to coverage ratio (0.0–1.0).

    Notes
    -----
    - Coverage is computed by intersecting Unicode blocks with script ranges.
    - Scripts with zero coverage are omitted from the result.
    - Returns empty mapping when no valid coverage is available.
    - Pure function: does not mutate inputs.
    """
    if not unicode_blocks or total_codepoints <= 0:
        return {}

    from collections import defaultdict

    script_counts: dict[str, int] = defaultdict(int)

    for block_name, count in unicode_blocks.items():
        block_range = UNICODE_BLOCK_RANGES.get(block_name)
        if block_range is None:
            continue

        b_start, b_end = block_range

        # assign block to first matching script (deterministic)
        for script, ranges in script_ranges.items():
            if any(b_start <= r_end and b_end >= r_start for r_start, r_end in ranges):
                script_counts[script] += count
                break

    return {
        script: cnt / total_codepoints
        for script, cnt in script_counts.items()
        if cnt > 0
    }


# TODO(#0): classification rule table will grow;
# refactor to data-driven mapping when script set expands
def infer_scripts(  # noqa: C901, PLR0912
    coverage: dict[str, Any], level: str = "medium"
) -> list[str]:
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
        A list of inferred ISO-15924 script codes (lowercase),
        ordered by decreasing confidence.
        Examples: "latn", "cyrl", "arab", "taml", "hani".
        Returns ``["unknown"]`` if no reliable inference is possible.
        The value ``"unknown"`` is a sentinel and must not be used
        for downstream language inference.
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
            # medium - default
            return count >= 20 or (count / total) >= 0.05

        scripts_score: dict[str, int] = {}

        def add_script(name: str, weight: int) -> None:
            scripts_score[name] = scripts_score.get(name, 0) + weight

        # --- block → script mapping (score-based)
        for block, count in blocks.items():
            # Latin needs strict significance (to avoid false multi-script noise),
            # but non-Latin scripts must be more sensitive: their block counts are
            # often smaller (or split across Extended/Supplement blocks).
            if block.startswith("Latin"):
                if not significant(count):
                    continue
            elif level == "conservative":
                if not (count >= 20 or (count / total) >= 0.05):
                    continue
            elif level == "aggressive":
                if count < 2:
                    continue
            elif not (count >= 5 or (count / total) >= 0.01):  # medium - default
                continue

            if block.startswith("Latin"):
                add_script("latn", count)
            elif block == "Greek and Coptic":
                add_script("grek", count)
            elif block == "Cyrillic":
                add_script("cyrl", count)
            elif block == "Arabic":
                add_script("arab", count)
            elif block == "Hebrew":
                add_script("hebr", count)
            elif block == "Devanagari":
                add_script("deva", count)
            elif block == "Bengali":
                add_script("beng", count)
            elif block == "Tamil":
                add_script("taml", count)
            elif block == "Thai":
                add_script("thai", count)
            elif block.startswith("Lao"):
                add_script("laoo", count)
            elif block in ("Hiragana", "Katakana"):
                add_script("jpan", count)
            elif block == "Hangul Syllables":
                add_script("hang", count)
            elif block == "Yi Syllables":
                add_script("yiii", count)
            elif block.startswith("Armenian"):
                add_script("armn", count)
            elif block.startswith("Georgian"):
                add_script("geor", count)
            elif block.startswith("Ethiopic"):
                add_script("ethi", count)
            elif block.startswith("Cherokee"):
                add_script("cher", count)
            elif block.startswith("Khmer"):
                add_script("khmr", count)
            elif block.startswith("Buginese"):
                add_script("bugi", count)
            elif block.startswith("Buhid"):
                add_script("buhd", count)
            elif block.startswith("Kana"):
                add_script("jpan", count)
            elif block.startswith("CJK Unified Ideographs"):
                add_script("hani", count)

            # --- CJK disambiguation (kept as a single-script outcome)
            if "hani" in scripts_score:
                if "jpan" in scripts_score:
                    return ["jpan"]
                if "hang" in scripts_score:
                    return ["hang"]
                return ["hani"]

        normalized_scores: list[tuple[str, int]] = []
        for name, score in scripts_score.items():
            iso = name
            normalized_scores.append((iso, score))

        if not normalized_scores:
            return ["unknown"]

        iso_priority: dict[str, int] = {
            "latn": 0,
            "grek": 1,
            "cyrl": 2,
            "arab": 3,
            "hebr": 4,
            "deva": 5,
            "beng": 6,
            "taml": 7,
            "thai": 8,
            "laoo": 9,
            "mymr": 10,
            "armn": 11,
            "geor": 12,
            "ethi": 13,
            "cher": 14,
            "khmr": 15,
            "bugi": 16,
            "buhd": 17,
            "yiii": 18,
            "jpan": 19,
            "hang": 20,
            "hani": 21,
        }

        normalized_scores.sort(key=lambda t: (-t[1], iso_priority.get(t[0], 999), t[0]))

        return [iso for iso, _ in normalized_scores]

    # -------------------------------
    # 2. Fallback: unicode.max
    # -------------------------------
    unicode_max = coverage.get("unicode", {}).get("max")
    if isinstance(unicode_max, int):
        if unicode_max <= 0x024F:
            return ["latn"]
        if 0x0370 <= unicode_max <= 0x03FF:
            return ["grek"]
        if 0x0400 <= unicode_max <= 0x04FF:
            return ["cyrl"]
        if 0x0590 <= unicode_max <= 0x05FF:
            return ["hebr"]
        if 0x0600 <= unicode_max <= 0x06FF:
            return ["arab"]
        if 0x0900 <= unicode_max <= 0x097F:
            return ["deva"]
        if unicode_max >= 0x4E00:
            return ["hani"]

    return ["unknown"]
