"""
Script coverage analysis helpers.

This module derives writing system coverage statistics from Unicode
coverage metadata.

Responsibilities
----------------
- Compute script coverage ratios from Unicode block coverage data.
- Map Unicode block coverage to script ranges defined in the ontology.
- Produce normalized script coverage metrics used by the inventory.

Design principles
-----------------
Script coverage analysis operates exclusively on Unicode coverage data
produced during earlier inventory stages. The functions are pure and
must not mutate input structures.

Architectural role
------------------
This module belongs to the **inventory subsystem** and performs script
coverage analysis used during metadata enrichment.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fontshow.ontology.unicode_tables import UNICODE_BLOCK_RANGES

if TYPE_CHECKING:
    from fontshow.core.types import ScriptISO


_UNICODE_BLOCK_SCRIPT_RULES: tuple[tuple[str, str, str], ...] = (
    ("prefix", "Latin", "latn"),
    ("exact", "Greek and Coptic", "grek"),
    ("exact", "Cyrillic", "cyrl"),
    ("exact", "Arabic", "arab"),
    ("exact", "Hebrew", "hebr"),
    ("exact", "Devanagari", "deva"),
    ("exact", "Dives Akuru", "diak"),
    ("exact", "Dogra", "dogr"),
    ("exact", "Bengali", "beng"),
    ("exact", "Tamil", "taml"),
    ("exact", "Thai", "thai"),
    ("prefix", "Lao", "laoo"),
    ("prefix", "Myanmar", "mymr"),
    ("exact", "Hiragana", "jpan"),
    ("exact", "Katakana", "jpan"),
    ("exact", "Hangul Syllables", "hang"),
    ("exact", "Yi Syllables", "yiii"),
    ("prefix", "Armenian", "armn"),
    ("prefix", "Georgian", "geor"),
    ("prefix", "Ethiopic", "ethi"),
    ("prefix", "Cherokee", "cher"),
    ("prefix", "Khmer", "khmr"),
    ("prefix", "Buginese", "bugi"),
    ("prefix", "Buhid", "buhd"),
    ("prefix", "Kana", "jpan"),
    ("prefix", "CJK Unified Ideographs", "hani"),
)

_UNICODE_MAX_FALLBACKS: tuple[tuple[int, int, str], ...] = (
    (0x0000, 0x024F, "latn"),
    (0x0370, 0x03FF, "grek"),
    (0x0400, 0x04FF, "cyrl"),
    (0x0590, 0x05FF, "hebr"),
    (0x0600, 0x06FF, "arab"),
    (0x0900, 0x097F, "deva"),
    (0x11800, 0x1184F, "dogr"),
    (0x11900, 0x1195F, "diak"),
)

_ISO_PRIORITY: dict[str, int] = {
    "latn": 0,
    "grek": 1,
    "cyrl": 2,
    "arab": 3,
    "hebr": 4,
    "deva": 5,
    "diak": 6,
    "dogr": 7,
    "beng": 8,
    "taml": 9,
    "thai": 10,
    "laoo": 11,
    "mymr": 12,
    "armn": 13,
    "geor": 14,
    "ethi": 15,
    "cher": 16,
    "khmr": 17,
    "bugi": 18,
    "buhd": 19,
    "yiii": 20,
    "jpan": 21,
    "hang": 22,
    "hani": 23,
}


def _is_significant_latin_block(count: int, total: int, level: str) -> bool:
    """
    Evaluate Latin-block significance for script inference.

    Parameters
    ----------
    count : int
        Covered codepoint count for the current Unicode block.
    total : int
        Total covered codepoint count across all Unicode blocks.
    level : str
        Inference aggressiveness level.

    Returns
    -------
    bool
        True when the Latin block should contribute to script inference.
    """
    if level == "conservative":
        return count >= 50 or (count / total) >= 0.10
    if level == "aggressive":
        return count >= 5
    return count >= 20 or (count / total) >= 0.05


def _is_significant_non_latin_block(count: int, total: int, level: str) -> bool:
    """
    Evaluate non-Latin block significance for script inference.

    Parameters
    ----------
    count : int
        Covered codepoint count for the current Unicode block.
    total : int
        Total covered codepoint count across all Unicode blocks.
    level : str
        Inference aggressiveness level.

    Returns
    -------
    bool
        True when the non-Latin block should contribute to script inference.
    """
    if level == "conservative":
        return count >= 20 or (count / total) >= 0.05
    if level == "aggressive":
        return count >= 2
    return count >= 5 or (count / total) >= 0.01


def _block_is_significant(block_name: str, count: int, total: int, level: str) -> bool:
    """
    Decide whether a Unicode block contributes evidence for script inference.

    Parameters
    ----------
    block_name : str
        Unicode block name as produced by coverage extraction.
    count : int
        Covered codepoint count for the current Unicode block.
    total : int
        Total covered codepoint count across all Unicode blocks.
    level : str
        Inference aggressiveness level.

    Returns
    -------
    bool
        True when the block count passes the level-dependent threshold.
    """
    if block_name.startswith("Latin"):
        return _is_significant_latin_block(count, total, level)
    return _is_significant_non_latin_block(count, total, level)


def _match_block_script(block_name: str) -> str | None:
    """
    Resolve a Unicode block name to an inferred ISO-15924 script tag.

    Parameters
    ----------
    block_name : str
        Unicode block name as produced by coverage extraction.

    Returns
    -------
    str | None
        Matching lowercase ISO-15924 script tag, or None when the block
        is not mapped by the inference table.
    """
    for match_kind, pattern, script in _UNICODE_BLOCK_SCRIPT_RULES:
        if match_kind == "exact" and block_name == pattern:
            return script
        if match_kind == "prefix" and block_name.startswith(pattern):
            return script
    return None


def _score_scripts_from_blocks(blocks: dict[str, int], level: str) -> dict[str, int]:
    """
    Score candidate scripts from Unicode block coverage.

    Parameters
    ----------
    blocks : dict[str, int]
        Mapping of Unicode block name to covered codepoint count.
    level : str
        Inference aggressiveness level.

    Returns
    -------
    dict[str, int]
        Weighted score per inferred script tag.
    """
    total = sum(blocks.values()) or 1
    scripts_score: dict[str, int] = {}

    for block, count in blocks.items():
        if not _block_is_significant(block, count, total, level):
            continue
        script = _match_block_script(block)
        if script is None:
            continue
        scripts_score[script] = scripts_score.get(script, 0) + count

    return scripts_score


def _collapse_cjk_scripts(scripts_score: dict[str, int]) -> list[str] | None:
    """
    Collapse CJK-related script evidence to a single preferred outcome.

    Parameters
    ----------
    scripts_score : dict[str, int]
        Weighted score per inferred script tag.

    Returns
    -------
    list[str] | None
        Single-item script result for CJK cases, or None when the scores
        do not require CJK collapse.
    """
    if "hani" not in scripts_score:
        return None
    if "jpan" in scripts_score:
        return ["jpan"]
    if "hang" in scripts_score:
        return ["hang"]
    return ["hani"]


def _sort_scored_scripts(scripts_score: dict[str, int]) -> list[str]:
    """
    Sort inferred scripts by confidence and deterministic tie-breakers.

    Parameters
    ----------
    scripts_score : dict[str, int]
        Weighted score per inferred script tag.

    Returns
    -------
    list[str]
        Sorted script tags, or ``["unknown"]`` when no scores are present.
    """
    if not scripts_score:
        return ["unknown"]

    normalized_scores = sorted(
        scripts_score.items(),
        key=lambda item: (-item[1], _ISO_PRIORITY.get(item[0], 999), item[0]),
    )
    return [iso for iso, _ in normalized_scores]


def _infer_from_unicode_max(unicode_max: Any) -> list[str]:
    """
    Infer a fallback script from the maximum covered codepoint.

    Parameters
    ----------
    unicode_max : Any
        Candidate maximum Unicode codepoint from the coverage payload.

    Returns
    -------
    list[str]
        Single-item inferred script list, or ``["unknown"]`` when no
        fallback mapping applies.
    """
    if not isinstance(unicode_max, int):
        return ["unknown"]

    for start, end, script in _UNICODE_MAX_FALLBACKS:
        if start <= unicode_max <= end:
            return [script]
    if unicode_max >= 0x4E00:
        return ["hani"]
    return ["unknown"]


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


def infer_scripts(coverage: dict[str, Any], level: str = "medium") -> list[str]:
    """
    Infer writing scripts from Unicode coverage metadata.

    The function follows a two-step strategy:

    1. **Primary path**: analyze ``coverage["unicode_blocks"]`` if present.
    2. **Fallback path**: infer from ``coverage["unicode"]["max"]``.

    Parameters
    ----------
    coverage : dict[str, Any]
        Coverage block extracted from a font entry. Expected keys are
        ``unicode_blocks`` (mapping block name to count) and/or
        ``unicode.max`` (maximum code point).
    level : str, optional
        Inference aggressiveness level. One of
        ``"conservative"``, ``"medium"`` (default), or ``"aggressive"``.

    Returns
    -------
    list[str]
        Inferred ISO-15924 script codes in lowercase, ordered by
        decreasing confidence. Returns ``["unknown"]`` if no reliable
        inference is possible.

    Notes
    -----
    Examples of returned script tags include ``"latn"``, ``"cyrl"``,
    ``"arab"``, ``"taml"``, and ``"hani"``. The value ``"unknown"``
    is a sentinel and must not be used for downstream language
    inference.
    """
    blocks: dict[str, int] = coverage.get("unicode_blocks", {}) or {}
    if blocks:
        scripts_score = _score_scripts_from_blocks(blocks, level)
        cjk_result = _collapse_cjk_scripts(scripts_score)
        if cjk_result is not None:
            return cjk_result
        return _sort_scored_scripts(scripts_score)

    return _infer_from_unicode_max(coverage.get("unicode", {}).get("max"))
