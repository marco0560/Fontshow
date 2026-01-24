import json

from fontshow.json_format import dumps_pretty
from fontshow.parse_font_inventory import parse_inventory
from fontshow.schema_validation import validate_inventory_schema
from fontshow.semantic_validation import validate_language_codes


def _minimal_inventory():
    """
    Minimal inventory structure that should always be valid.
    Used to verify catalog output invariants.
    """
    return {
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


def test_enriched_inventory_is_schema_valid():
    """
    Catalog output MUST always conform to inventory schema.
    """
    data = _minimal_inventory()
    enriched = parse_inventory(data, level="medium")

    # Structural invariants
    assert "metadata" in enriched
    assert enriched["metadata"]["schema_version"] == "1.1"
    assert "fonts" in enriched

    # Schema validation must succeed
    validate_inventory_schema(enriched)


def test_catalog_json_roundtrip_preserves_validity():
    """
    JSON serialization must not corrupt schema validity.
    """
    data = _minimal_inventory()
    enriched = parse_inventory(data, level="medium")

    rendered = dumps_pretty(enriched, indent=2, ensure_ascii=False)
    parsed = json.loads(rendered)

    validate_inventory_schema(parsed)


def test_language_codes_have_no_warnings_for_minimal_case():
    """
    Semantic validation should not emit warnings for
    a minimal, valid inventory.
    """
    data = _minimal_inventory()
    enriched = parse_inventory(data, level="medium")

    warnings = validate_language_codes(enriched)
    assert warnings == []
