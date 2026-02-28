from fontshow.parse_font_inventory import parse_inventory
from fontshow.types import Severity


def test_parse_inventory_basic_latin_only():
    data = {
        "fonts": [
            {
                "coverage": {
                    "unicode_blocks": {
                        "Basic Latin": 95,
                    }
                }
            }
        ]
    }

    result = parse_inventory(data, level="medium")
    inference = result["fonts"][0]["inference"]

    assert inference["languages"] == []


def test_parse_inventory_latin_extended():
    data = {
        "fonts": [
            {
                "coverage": {
                    "unicode_blocks": {
                        "Basic Latin": 95,
                        "Latin-1 Supplement": 96,
                    }
                }
            }
        ]
    }

    result = parse_inventory(data, level="medium")
    inference = result["fonts"][0]["inference"]

    assert "en" in inference["languages"]
    assert "fr" in inference["languages"]
    assert "de" in inference["languages"]


def test_declared_languages_do_not_affect_inference():
    data = {
        "fonts": [
            {
                "coverage": {
                    "languages": ["fr", "de"],
                    "unicode_blocks": {
                        "Basic Latin": 95,
                    },
                }
            }
        ]
    }

    result = parse_inventory(data, level="medium")
    inference = result["fonts"][0]["inference"]

    # declared preserved
    assert inference["declared_languages"] == ["fr", "de"]

    # inferred remains strict
    assert inference["languages"] == []


def test_parse_inventory_cyrillic():
    data = {
        "fonts": [
            {
                "coverage": {
                    "unicode_blocks": {
                        "Cyrillic": 128,
                    }
                }
            }
        ]
    }

    result = parse_inventory(data, level="medium")
    inference = result["fonts"][0]["inference"]

    assert "ru" in inference["languages"]


def test_parse_inventory_no_coverage():
    data = {"fonts": [{"coverage": {}}]}

    result = parse_inventory(data, level="medium")
    inference = result["fonts"][0]["inference"]

    assert inference["languages"] == []


def test_missing_declared_languages_emits_info_warning():
    data = {"fonts": [{"coverage": {"unicode_blocks": {"Basic Latin": 95}}}]}

    result = parse_inventory(data, level="medium")
    warnings = result["fonts"][0].get("warnings", [])

    assert any(
        w["code"] == "missing_declared_languages" and w["severity"] == Severity.INFO
        for w in warnings
    )
