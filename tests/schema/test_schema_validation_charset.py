from fontshow.schema_validation import validate_inventory_schema


def test_schema_validation_with_charset_enrichment():
    inventory = {
        "schema_version": "1.1",
        "fonts": [
            {
                "path": "/fake/font.ttf",
                "identity": {
                    "family": "Fake",
                    "style": "Regular",
                },
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
            }
        ],
    }

    warnings = validate_inventory_schema(inventory)

    # Schema validation must succeed without errors or critical warnings
    assert all(w["severity"] in {"info", "warning"} for w in warnings)
