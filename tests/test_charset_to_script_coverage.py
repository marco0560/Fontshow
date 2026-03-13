"""
Verify conversion from Unicode block coverage to script coverage.

Responsibilities
----------------
- Ensure script coverage is correctly derived from Unicode block data.
- Validate that unrelated scripts are not reported.

Design principles
-----------------
Coverage tests rely on minimal synthetic Unicode block maps so that
coverage calculations remain deterministic.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
the logic that derives script coverage from Unicode block statistics.
"""

from fontshow.inventory.script_analysis import script_coverage_from_unicode_blocks


def test_script_coverage_basic_latin_only():
    """
    Verify that Basic Latin coverage maps entirely to the Latin script.

    Returns
    -------
    None
    """
    unicode_blocks = {"Basic Latin": 95}

    script_ranges = {
        "LATN": [(0x0000, 0x007F)],
        "GREK": [(0x0370, 0x03FF)],
    }

    result = script_coverage_from_unicode_blocks(
        unicode_blocks,
        script_ranges,
        total_codepoints=95,
    )

    assert result == {"LATN": 1.0}


def test_parse_inventory_adds_script_coverage_from_charset(enable_fontshow_logging):
    """
    Verify that parse-inventory derives script coverage from charset ranges.

    Parameters
    ----------
    enable_fontshow_logging : object
        Logging fixture used by the parse-inventory execution path.

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
    assert "script_coverage_from_charset" in cov
    assert "LATN" in cov["script_coverage_from_charset"]
