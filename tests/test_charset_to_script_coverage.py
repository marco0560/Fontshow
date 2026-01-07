from fontshow.parse_font_inventory import script_coverage_from_unicode_blocks


def test_script_coverage_basic_latin_only():
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
    import importlib

    import fontshow.parse_font_inventory

    importlib.reload(fontshow.parse_font_inventory)

    inventory = {
        "schema_version": "1.0",
        "fonts": [
            {
                "path": "/fake/font.ttf",
                "identity": {"family": "Fake", "style": "Regular"},
                "coverage": {
                    "charset": {
                        "source": "fontconfig",
                        "ranges": [[0x0020, 0x007E]],
                    }
                },
            }
        ],
    }

    fontshow.parse_font_inventory.parse_inventory(inventory, level="medium")

    cov = inventory["fonts"][0]["coverage"]
    assert "script_coverage_from_charset" in cov
    assert "LATN" in cov["script_coverage_from_charset"]
