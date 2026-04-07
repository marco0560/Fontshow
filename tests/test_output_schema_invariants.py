"""
Verify output schema invariants.

Responsibilities
----------------
- Ensure parsed inventory outputs remain schema-valid.
- Validate structural invariants expected by the inventory schema.

Design principles
----------------
Invariant tests construct minimal inventories to ensure schema
compliance checks remain deterministic.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
that parsed inventory outputs maintain schema invariants.
"""

import json

from fontshow.cli.parse_inventory import parse_inventory
from fontshow.core.json_format import dumps_pretty
from fontshow.inventory.schema_validation import validate_inventory_schema

# ---------------------------------------------------------------------------
# Minimal valid v1.5 inventory
# ---------------------------------------------------------------------------


def _minimal_inventory():
    """
    Minimal inventory structure that is schema-valid for v1.5.

    Used to verify output invariants.

    Parameters
    ----------
    None

    Returns
    -------
    dict
        Minimal schema-valid inventory payload for parse-inventory tests.
    """
    return {
        "metadata": {
            "schema_version": "1.5",
            "input_inventory_tool": "test",
            "input_inventory_tool_version": "0",
            "inference_level": "none",
            "fonttools": {
                "available": True,
                "version": "0",
                "fontconfig_charset_included": False,
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
            "validation": {
                "lualatex": {
                    "attempted": False,
                    "engine": None,
                    "engine_version": None,
                    "luaotfload_version": None,
                    "fontspec_version": None,
                    "polyglossia_version": None,
                    "runtime_fingerprint": None,
                    "render_policy_version": "test-policy",
                }
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
                "metrics": {
                    "units_per_em": 1000,
                    "ascent": 800,
                    "descent": -200,
                    "weight_class": 400,
                    "width_class": 5,
                    "italic_angle": 0,
                    "is_fixed_pitch": False,
                    "glyph_count": 100,
                },
                "coverage": {
                    "unicode_blocks": {
                        "Basic Latin": 95,
                    }
                },
                "inference": {},
                "charset": {},
                "typography": {
                    "sample_text": {"source": "font", "text": "Fake sample"},
                    "specimen_text": "Fake specimen",
                    "specimen_strategy": "cmap",
                    "specimen_glyph_count": 50,
                    "specimen_rejection_reason": None,
                    "primary_script": None,
                    "script_display_name": None,
                    "render_policy": {
                        "polyglossia_language": None,
                        "fontspec_opts": None,
                    },
                    "script_source": None,
                },
                "loadability": {
                    "lualatex": {
                        "attempted": False,
                        "loadable": None,
                        "reason": None,
                        "runtime_fingerprint": None,
                        "probe_input": None,
                        "render_variants": [],
                    }
                },
            }
        ],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_enriched_inventory_is_schema_valid():
    """
    Output MUST conform to schema v1.4.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    data = _minimal_inventory()
    enriched = parse_inventory(data, level="medium")

    assert "metadata" in enriched
    assert enriched["metadata"]["schema_version"] == "1.5"
    assert "fonts" in enriched

    # Schema validation must run on JSON-rendered output (Enums → strings)
    rendered = dumps_pretty(enriched, indent=2, ensure_ascii=False)
    parsed = json.loads(rendered)

    warnings = validate_inventory_schema(parsed)
    assert warnings == []


def test_catalog_json_roundtrip_preserves_validity():
    """
    JSON serialization must not corrupt schema validity.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    data = _minimal_inventory()
    enriched = parse_inventory(data, level="medium")

    rendered = dumps_pretty(enriched, indent=2, ensure_ascii=False)
    parsed = json.loads(rendered)

    rendered = dumps_pretty(enriched, indent=2, ensure_ascii=False)
    parsed = json.loads(rendered)
    warnings = validate_inventory_schema(parsed)
    assert warnings == []


def test_language_codes_have_no_warnings_for_minimal_case():
    """
    Semantic validation should emit no warnings for minimal valid inventory.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    data = _minimal_inventory()
    enriched = parse_inventory(data, level="medium")

    rendered = dumps_pretty(enriched, indent=2, ensure_ascii=False)
    parsed = json.loads(rendered)
    warnings = validate_inventory_schema(parsed)
    assert warnings == []
