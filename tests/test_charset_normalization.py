"""
Verify charset normalization utilities.

Responsibilities
----------------
- Ensure charset ranges are merged and sorted correctly.
- Validate computation of derived Unicode block coverage.

Design principles
-----------------
Normalization tests use small synthetic range sets so that merging,
sorting, and coverage calculations are deterministic.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
utility functions that normalize charset range information.
"""

from fontshow.unicode.charset_ranges import (
    normalize_charset_ranges,
    unicode_blocks_from_charset_ranges,
)


def test_normalize_charset_merges_and_sorts():
    """
    Verify that overlapping and adjacent ranges are merged after sorting.

    Returns
    -------
    None
    """
    ranges = [
        [10, 20],
        [1, 5],
        [6, 9],  # adjacent to [1,5]
        [15, 30],  # overlaps with [10,20]
    ]

    result = normalize_charset_ranges(ranges)

    assert result["ranges"] == [[1, 30]]
    assert result["codepoints_count"] == 30


def test_normalize_charset_disjoint_ranges():
    """
    Verify that disjoint charset ranges remain separate after normalization.

    Returns
    -------
    None
    """
    ranges = [
        [1, 3],
        [10, 12],
    ]

    result = normalize_charset_ranges(ranges)

    assert result["ranges"] == [[1, 3], [10, 12]]
    assert result["codepoints_count"] == (3 - 1 + 1) + (12 - 10 + 1)


def test_normalize_charset_empty():
    """
    Verify that normalizing an empty range list yields an empty result.

    Returns
    -------
    None
    """
    result = normalize_charset_ranges([])

    assert result["ranges"] == []
    assert result["codepoints_count"] == 0


def test_parse_inventory_adds_normalized_charset(enable_fontshow_logging):
    """
    Verify that parse-inventory adds normalized charset coverage data.

    Parameters
    ----------
    enable_fontshow_logging : object
        Logging fixture enabling the parse-inventory path used by this test.

    Returns
    -------
    None

    Notes
    -----
    The test builds a minimal inventory and asserts that adjacent ranges
    are merged into a single normalized charset block.
    """
    import importlib

    import fontshow.cli.parse_inventory
    from tests.helpers import minimal_font_entry_v12, minimal_inventory_v12

    importlib.reload(fontshow.cli.parse_inventory)

    inventory = minimal_inventory_v12()
    font = minimal_font_entry_v12()

    font["charset"] = {
        "source": "fontconfig",
        "ranges": [[1, 3], [4, 5]],
    }

    inventory["fonts"] = [font]

    fontshow.cli.parse_inventory.parse_inventory(inventory, level="medium")

    cov = inventory["fonts"][0]["coverage"]
    assert "normalized_charset" in cov
    assert cov["normalized_charset"]["ranges"] == [[1, 5]]


def test_unicode_blocks_from_charset_basic_latin():
    """
    Verify that Basic Latin coverage is counted correctly from ranges.

    Returns
    -------
    None
    """
    ranges = [[0x0020, 0x007E]]
    blocks = unicode_blocks_from_charset_ranges(ranges)

    assert blocks["Basic Latin"] == 0x007E - 0x0020 + 1


def test_parse_inventory_adds_unicode_blocks_from_charset(enable_fontshow_logging):
    """
    Verify that parse-inventory derives Unicode block coverage from charset ranges.

    Parameters
    ----------
    enable_fontshow_logging : object
        Logging fixture enabling the parse-inventory path used by this test.

    Returns
    -------
    None
    """
    import importlib

    import fontshow.cli.parse_inventory

    importlib.reload(fontshow.cli.parse_inventory)

    from tests.helpers import minimal_font_entry_v12, minimal_inventory_v12

    inventory = minimal_inventory_v12()
    font = minimal_font_entry_v12()

    font["charset"] = {
        "source": "fontconfig",
        "ranges": [[0x0020, 0x007E]],
    }

    inventory["fonts"] = [font]
    fontshow.cli.parse_inventory.parse_inventory(inventory, level="medium")

    cov = inventory["fonts"][0]["coverage"]
    assert "unicode_blocks_from_charset" in cov
    assert "Basic Latin" in cov["unicode_blocks_from_charset"]
