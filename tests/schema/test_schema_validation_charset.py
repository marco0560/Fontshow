from fontshow.schema_validation import validate_inventory_schema
from fontshow.types import Severity

# ---------------------------------------------------------------------------
# Helper — minimal valid v1.2 inventory with charset enrichment
# ---------------------------------------------------------------------------


def _base_inventory_with_charset():
    return {
        "metadata": {
            "schema_version": "1.2",
            "input_inventory_tool": "test",
            "input_inventory_tool_version": "0",
            "inference_level": "none",
            "fonttools": {
                "available": True,
                "version": "0",
                "fontconfig_charset_included": True,
            },
            "run_environment": {
                "os": "test",
                "os_release": "test",
                "kernel": "test",
                "machine": "test",
                "python_version": "test",
                "hostname": "test",
                "execution_context": "native",
            },
        },
        "fonts": [
            {
                "path": "/fake/font.ttf",
                "family": "Fake",
                "subfamily": "Regular",
                "typographic_subfamily": None,
                "full_name": "Fake Regular",
                "postscript_name": "Fake-Regular",
                "version_string": "1.0",
                "unique_font_id": "fake-regular",
                "units_per_em": 1000,
                "ascent": 800,
                "descent": -200,
                "weight_class": 400,
                "width_class": 5,
                "italic_angle": 0,
                "is_fixed_pitch": False,
                "glyph_count": 100,
                "coverage": {
                    "normalized_charset": {
                        "ranges": [[32, 126]],
                        "codepoints_count": 95,
                    },
                    "unicode_blocks_from_charset": {
                        "Basic Latin": 95,
                    },
                    "script_coverage_from_charset": {
                        "LATN": 1.0,
                    },
                },
                "inference": {},
                "charset": {},
                "sample_text": {"source": "font", "text": "Fake sample"},
                "specimen_text": "Fake specimen",
                "specimen_strategy": "cmap",
                "specimen_glyph_count": 50,
                "specimen_rejection_reason": None,
            }
        ],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_schema_validation_with_charset_enrichment():
    inventory = _base_inventory_with_charset()

    warnings = validate_inventory_schema(inventory)

    # Must not emit ERROR severity for valid schema
    assert all(w["severity"] != Severity.ERROR for w in warnings)


def test_schema_validation_no_spurious_warnings():
    inventory = _base_inventory_with_charset()

    warnings = validate_inventory_schema(inventory)

    # Valid v1.2 inventory must produce no warnings
    assert warnings == []
