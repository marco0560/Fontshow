"""
Charset range decoding utilities.

Extracted from parse_font_inventory to isolate pure Unicode logic.

These helpers operate purely on charset bitmaps and codepoint ranges
and therefore belong in the unicode domain layer.
"""

from __future__ import annotations

from typing import Any

from fontshow.unicode_tables import UNICODE_BLOCK_RANGES


def decode_fc_charset_bitmap(raw: str) -> list[list[int]]:
    """
    Decode a FontConfig charset bitmap into Unicode codepoint ranges.

    Parameters
    ----------
    raw : str
        Raw multiline charset bitmap produced by fc-query.

    Returns
    -------
    list[list[int]]
        Sorted, merged [start, end] Unicode ranges (inclusive).

    Notes
    -----
    The input is the raw multiline bitmap produced by fc-query, e.g.:

    0000: 00000000 ffffffff ffffffff 7fffffff ...
    0001: ffffffff ...

    - Each input line encodes 256 codepoints:
        block_index * 256
        8 words of 32 bits
        bits interpreted MSB → LSB
    - Invalid lines or malformed words are skipped safely.
    - Output ranges are deduplicated, sorted, and merged.
    - Pure function: does not mutate external state.
    """
    codepoints: list[int] = []

    for line in raw.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue

        block_hex, rest = line.split(":", 1)
        try:
            block_index = int(block_hex.strip(), 16)
        except ValueError:
            continue

        words = rest.strip().split()
        if len(words) != 8:
            continue

        base = block_index * 256

        for word_index, word_hex in enumerate(words):
            try:
                word = int(word_hex, 16)
            except ValueError:
                continue

            for bit in range(32):
                if word & (1 << (31 - bit)):
                    codepoints.append(base + word_index * 32 + bit)

    if not codepoints:
        return []

    codepoints = sorted(set(codepoints))

    ranges: list[list[int]] = []
    start = prev = codepoints[0]

    for cp in codepoints[1:]:
        if cp == prev + 1:
            prev = cp
        else:
            ranges.append([start, prev])
            start = prev = cp

    ranges.append([start, prev])
    return ranges


def unicode_blocks_from_charset_ranges(
    ranges: list[list[int]],
) -> dict[str, int]:
    """
    Derive Unicode block coverage counts from normalized charset ranges.

    Parameters
    ----------
    ranges : list[list[int]]
        Normalized [start, end] Unicode codepoint ranges (inclusive).

    Returns
    -------
    dict[str, int]
        Mapping of Unicode block name to covered codepoint count.

    Notes
    -----
    - Coverage is computed by intersecting each input range with
      known Unicode block boundaries.
    - Counts are inclusive and accumulated across overlapping ranges.
    - Pure function: does not mutate input.
    """
    blocks: dict[str, int] = {}

    for r_start, r_end in ranges:
        for block_name, (b_start, b_end) in UNICODE_BLOCK_RANGES.items():
            start = max(r_start, b_start)
            end = min(r_end, b_end)
            if start <= end:
                blocks[block_name] = blocks.get(block_name, 0) + (end - start + 1)

    return blocks


def normalize_charset_ranges(ranges: list[list[int]]) -> dict[str, Any]:
    """
    Normalize a list of Unicode codepoint ranges.

    Parameters
    ----------
    ranges : list[list[int]]
        List of [start, end] Unicode codepoint ranges (inclusive).

    Returns
    -------
    dict[str, Any]
        {
            "ranges": list[list[int]]
                Normalized, sorted, and merged ranges.
            "codepoints_count": int
                Total number of covered Unicode codepoints (inclusive).
        }

    Notes
    -----
    - Ranges are sorted by start codepoint before normalization.
    - Overlapping and adjacent ranges are merged.
    - Result is deterministic and idempotent.
    - Pure function: does not mutate inputs.
    """
    if not ranges:
        return {"ranges": [], "codepoints_count": 0}

    # Defensive copy + sort
    ordered = sorted((int(a), int(b)) for a, b in ranges)

    merged: list[list[int]] = []
    cur_start, cur_end = ordered[0]

    for start, end in ordered[1:]:
        if start <= cur_end + 1:
            cur_end = max(cur_end, end)
        else:
            merged.append([cur_start, cur_end])
            cur_start, cur_end = start, end

    merged.append([cur_start, cur_end])

    codepoints_count = sum(end - start + 1 for start, end in merged)

    return {
        "ranges": merged,
        "codepoints_count": codepoints_count,
    }
