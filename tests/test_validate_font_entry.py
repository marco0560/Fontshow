"""
Verify validation of font inventory entries.

Responsibilities
----------------
- Ensure minimal valid entries pass validation.
- Verify structural errors are detected for malformed entries.

Design principles
----------------
Validation tests construct minimal inventory entries so that schema
and structural validation rules can be verified deterministically.

Architectural role
------------------
This module belongs to the **test infrastructure layer** and verifies
validation logic for individual font inventory entries.
"""

from fontshow.inventory.entry_validation import validate_font_entry
from fontshow.inventory.validation import has_style_leak_in_family
from tests.helpers import minimal_font_entry_v12

# ============================================================
# VALID MINIMAL ENTRY
# ============================================================


def test_validate_font_entry_valid_minimal():
    """
    Verify that the minimal valid current-schema font entry passes unchanged.

    Important setup assumption: `minimal_font_entry_v12()` returns a
    structurally complete entry acceptable to `validate_font_entry`.

    Returns
    -------
    None
    """
    entry = minimal_font_entry_v12()

    errors = validate_font_entry(entry, index=0)
    assert errors == []


# ============================================================
# NOT A DICT
# ============================================================


def test_validate_font_entry_not_a_dict():
    """
    Verify that non-dictionary inputs are rejected as invalid entries.

    Returns
    -------
    None
    """
    entry = "not a dict"

    errors = validate_font_entry(entry, index=0)
    assert errors  # must contain at least one error


# ============================================================
# MISSING REQUIRED FIELDS → FATAL
# ============================================================


def test_validate_font_entry_missing_required_fields():
    """
    Verify that missing required structural fields produce fatal errors.

    This test exercises the edge case of a partially populated mapping
    that contains only a path and omits required schema 1.2 fields.

    Returns
    -------
    None
    """
    entry = {
        "path": "/tmp/font.ttf"
        # missing required structural fields like family/subfamily/etc.
    }

    errors = validate_font_entry(entry, index=0)
    assert errors  # fatal structural error expected


def test_validate_font_entry_missing_family_is_fatal():
    """
    Verify that removing the required ``family`` field is fatal.

    Returns
    -------
    None
    """
    entry = minimal_font_entry_v12()
    entry.pop("family", None)

    errors = validate_font_entry(entry, index=0)
    assert errors
    assert "Missing or invalid 'family'" in errors


def test_style_leak_heuristic_ignores_justified_family_tokens():
    """
    Verify that family tokens matching width/weight metadata are not flagged.

    Returns
    -------
    None
    """
    entry = minimal_font_entry_v12()
    entry["family"] = "Roboto Condensed"
    entry["subfamily"] = "Bold"
    entry["metrics"]["weight_class"] = 700
    entry["metrics"]["width_class"] = 3

    assert has_style_leak_in_family(entry) is False


def test_style_leak_heuristic_flags_unjustified_family_tokens():
    """
    Verify that family tokens contradicting metadata are still flagged.

    Returns
    -------
    None
    """
    entry = minimal_font_entry_v12()
    entry["family"] = "Arial Black"
    entry["subfamily"] = "Regular"
    entry["metrics"]["weight_class"] = 400
    entry["metrics"]["width_class"] = 5
    entry["metrics"]["italic_angle"] = 0

    assert has_style_leak_in_family(entry) is True
