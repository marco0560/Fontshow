from fontshow.unicode.charset_ranges import (
    normalize_charset_ranges,
    unicode_blocks_from_charset_ranges,
)


def test_normalize_charset_merges_and_sorts():
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
    ranges = [
        [1, 3],
        [10, 12],
    ]

    result = normalize_charset_ranges(ranges)

    assert result["ranges"] == [[1, 3], [10, 12]]
    assert result["codepoints_count"] == (3 - 1 + 1) + (12 - 10 + 1)


def test_normalize_charset_empty():
    result = normalize_charset_ranges([])

    assert result["ranges"] == []
    assert result["codepoints_count"] == 0


def test_parse_inventory_adds_normalized_charset(enable_fontshow_logging):
    import importlib

    import fontshow.parse_font_inventory
    from tests.helpers import minimal_font_entry_v12, minimal_inventory_v12

    importlib.reload(fontshow.parse_font_inventory)

    inventory = minimal_inventory_v12()
    font = minimal_font_entry_v12()

    font["charset"] = {
        "source": "fontconfig",
        "ranges": [[1, 3], [4, 5]],
    }

    inventory["fonts"] = [font]

    fontshow.parse_font_inventory.parse_inventory(inventory, level="medium")

    cov = inventory["fonts"][0]["coverage"]
    assert "normalized_charset" in cov
    assert cov["normalized_charset"]["ranges"] == [[1, 5]]


def test_unicode_blocks_from_charset_basic_latin():
    ranges = [[0x0020, 0x007E]]
    blocks = unicode_blocks_from_charset_ranges(ranges)

    assert blocks["Basic Latin"] == 0x007E - 0x0020 + 1


def test_parse_inventory_adds_unicode_blocks_from_charset(enable_fontshow_logging):
    import importlib

    import fontshow.parse_font_inventory

    importlib.reload(fontshow.parse_font_inventory)

    from tests.helpers import minimal_font_entry_v12, minimal_inventory_v12

    inventory = minimal_inventory_v12()
    font = minimal_font_entry_v12()

    font["charset"] = {
        "source": "fontconfig",
        "ranges": [[0x0020, 0x007E]],
    }

    inventory["fonts"] = [font]
    fontshow.parse_font_inventory.parse_inventory(inventory, level="medium")

    cov = inventory["fonts"][0]["coverage"]
    assert "unicode_blocks_from_charset" in cov
    assert "Basic Latin" in cov["unicode_blocks_from_charset"]
