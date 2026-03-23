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

from functools import lru_cache
from typing import Any

from fontshow.core.types import ScriptISO
from fontshow.ontology.language_tables import SCRIPT_INFO
from fontshow.ontology.unicode_tables import UNICODE_BLOCK_RANGES


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


@lru_cache(maxsize=1)
def _script_priority_map() -> dict[str, int]:
    """
    Build deterministic script-priority mapping from ontology data.

    Returns
    -------
    dict[str, int]
        Lowercase script tag to inference priority.
    """
    return {
        str(script_iso).lower(): int(info["inference_priority"])
        for script_iso, info in SCRIPT_INFO.items()
    }


def _block_matches_pattern(block_name: str, pattern: str, match_mode: str) -> bool:
    """
    Check whether a Unicode block name satisfies a script rule pattern.

    Parameters
    ----------
    block_name : str
        Unicode block name extracted from coverage metadata.
    pattern : str
        Exact or prefix pattern stored in the ontology.
    match_mode : str
        Matching mode. Supported values are ``"exact"`` and ``"prefix"``.

    Returns
    -------
    bool
        True when the block matches the configured pattern.
    """
    if match_mode == "prefix":
        return block_name.startswith(pattern)
    return block_name == pattern


def _script_matches_block(script_iso: ScriptISO, block_name: str) -> bool:
    """
    Determine whether a block contributes evidence for a script.

    Parameters
    ----------
    script_iso : ScriptISO
        Script being evaluated.
    block_name : str
        Unicode block name extracted from coverage metadata.

    Returns
    -------
    bool
        True when the block matches either required or optional patterns.
    """
    info = SCRIPT_INFO[script_iso]
    patterns = list(info["required_blocks"]) + list(info["optional_blocks"])
    match_mode = str(info["block_match"])
    return any(
        _block_matches_pattern(block_name, pattern, match_mode) for pattern in patterns
    )


def _script_block_score(
    script_iso: ScriptISO, blocks: dict[str, int], level: str
) -> int:
    """
    Score a script from block coverage using required/optional evidence.

    Parameters
    ----------
    script_iso : ScriptISO
        Script being evaluated.
    blocks : dict[str, int]
        Mapping of Unicode block name to covered codepoint count.
    level : str
        Inference aggressiveness level.

    Returns
    -------
    int
        Weighted score for the script. Returns ``0`` when no required
        block evidence is present.
    """
    info = SCRIPT_INFO[script_iso]
    match_mode = str(info["block_match"])
    total = sum(blocks.values()) or 1
    required_score = 0
    optional_score = 0

    for block_name, count in blocks.items():
        if not _block_is_significant(block_name, count, total, level):
            continue

        if any(
            _block_matches_pattern(block_name, pattern, match_mode)
            for pattern in info["required_blocks"]
        ):
            required_score += count
            continue

        if any(
            _block_matches_pattern(block_name, pattern, match_mode)
            for pattern in info["optional_blocks"]
        ):
            optional_score += count

    if required_score <= 0:
        return 0

    return required_score + optional_score


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
    scripts_score: dict[str, int] = {}

    for script_iso in SCRIPT_INFO:
        script_tag = str(script_iso).lower()
        matched_count = _script_block_score(script_iso, blocks, level)

        if matched_count > 0:
            scripts_score[script_tag] = matched_count

    return scripts_score


def _apply_preferred_over(scripts_score: dict[str, int]) -> dict[str, int]:
    """
    Apply ontology-driven soft precedence between competing scripts.

    Parameters
    ----------
    scripts_score : dict[str, int]
        Weighted score per inferred script tag.

    Returns
    -------
    dict[str, int]
        Updated score mapping after soft precedence adjustments.
    """
    adjusted = dict(scripts_score)

    for script_tag, score in list(adjusted.items()):
        info = SCRIPT_INFO[ScriptISO(script_tag.upper())]
        for preferred_iso in info["preferred_over"]:
            preferred_tag = str(preferred_iso).lower()
            if preferred_tag not in adjusted:
                continue
            if score >= adjusted[preferred_tag]:
                adjusted.pop(preferred_tag, None)

    return adjusted


def _apply_suppressions(scripts_score: dict[str, int]) -> dict[str, int]:
    """
    Apply ontology-driven hard suppressions between competing scripts.

    Parameters
    ----------
    scripts_score : dict[str, int]
        Weighted score per inferred script tag.

    Returns
    -------
    dict[str, int]
        Updated score mapping after hard suppressions.
    """
    adjusted = dict(scripts_score)

    for script_tag in list(adjusted):
        if script_tag not in adjusted:
            continue
        info = SCRIPT_INFO[ScriptISO(script_tag.upper())]
        if adjusted[script_tag] <= 0:
            continue
        for suppressed_iso in info["suppresses"]:
            adjusted.pop(str(suppressed_iso).lower(), None)

    return adjusted


def _collapse_script_groups(scripts_score: dict[str, int]) -> dict[str, int]:
    """
    Collapse ontology-defined script groups to a canonical representative.

    Parameters
    ----------
    scripts_score : dict[str, int]
        Weighted score per inferred script tag.

    Returns
    -------
    dict[str, int]
        Score mapping after group-level collapse.
    """
    adjusted = dict(scripts_score)
    groups: dict[str, list[str]] = {}

    for script_tag in adjusted:
        group = str(
            SCRIPT_INFO[ScriptISO(script_tag.upper())]["collapse_group"]
        ).strip()
        if not group:
            continue
        groups.setdefault(group.lower(), []).append(script_tag)

    for group_tag, members in groups.items():
        if len(members) <= 1:
            continue
        target_tag = group_tag
        if target_tag not in adjusted:
            adjusted[target_tag] = max(adjusted[m] for m in members)
        for member in members:
            if member != target_tag:
                adjusted.pop(member, None)

    return adjusted


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

    priority_map = _script_priority_map()
    normalized_scores = sorted(
        scripts_score.items(),
        key=lambda item: (-item[1], priority_map.get(item[0], 999), item[0]),
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

    matches: list[tuple[int, str]] = []

    for script_iso, info in SCRIPT_INFO.items():
        script_tag = str(script_iso).lower()
        for start, end in info["unicode_max_ranges"]:
            if start <= unicode_max <= end:
                matches.append((int(info["inference_priority"]), script_tag))

    if matches:
        matches.sort()
        return [matches[0][1]]

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
        scripts_score = _apply_preferred_over(scripts_score)
        scripts_score = _apply_suppressions(scripts_score)
        scripts_score = _collapse_script_groups(scripts_score)
        return _sort_scored_scripts(scripts_score)

    return _infer_from_unicode_max(coverage.get("unicode", {}).get("max"))
