import json

from fontshow.json_format import dumps_pretty
from fontshow.parse_font_inventory import parse_inventory
from fontshow.schema_validation import validate_inventory_schema
from fontshow.semantic_validation import validate_language_codes


def test_enriched_inventory_output_is_schema_valid():
    # Minimal input already consistent with existing parse_inventory tests
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

    enriched = parse_inventory(data, level="medium")

    # Output-contract invariants
    assert "metadata" in enriched
    assert enriched["metadata"]["schema_version"] == "1.1"
    assert "fonts" in enriched

    # Structural invariant: schema validation must pass
    validate_inventory_schema(enriched)


def test_pretty_json_roundtrip_preserves_schema_validity():
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

    enriched = parse_inventory(data, level="medium")

    rendered = dumps_pretty(enriched, indent=2, ensure_ascii=False)
    parsed_back = json.loads(rendered)

    # Schema must still validate after formatting + round-trip
    validate_inventory_schema(parsed_back)


def test_semantic_language_codes_have_no_warnings_for_minimal_case():
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

    enriched = parse_inventory(data, level="medium")

    warnings = validate_language_codes(enriched)
    assert warnings == []
