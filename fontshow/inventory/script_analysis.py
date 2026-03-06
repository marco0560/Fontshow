"""
Script coverage analysis utilities for inventory processing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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
